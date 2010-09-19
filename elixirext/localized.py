from sqlalchemy            import Table, Column, and_, desc, ForeignKey
from sqlalchemy.orm        import mapper, MapperExtension, EXT_CONTINUE, \
                                  object_session, relation

from elixir                import Integer, DateTime
from elixir                import Unicode
from elixir.statements     import Statement
from elixir.properties     import EntityBuilder
from elixir.entity         import getmembers

__all__ = ['acts_as_localized']
__doc_all__ = []





def entity_polymorph_class(entity):
    """
    """
    for class_ in entity.__mro__[1:]:
        descriptor = getattr(class_, '_descriptor', False) # EntityBase has no _descriptor
        if descriptor and  getattr(class_._descriptor, 'table', None) is not None:
            return class_
    return False
#
# the acts_as_versioned statement
#
class LocalizedEntityBuilder(EntityBuilder):

    def __init__(self, entity, for_fields=[], default_locale=u'en'):
        self.entity = entity
        entity.__localized_fields__ = for_fields
        self.default_locale = default_locale

    def create_non_pk_cols(self):
        """ non primary key columns
        """
        self.add_table_column(Column('default_locale', Unicode,
                                     default=self.default_locale))

    # we copy columns from the main entity table, so we need it to exist first
    def after_table(self):

        entity = self.entity

        def localized_init(self, **kw):
            self.__dict__.update(kw)

        # create a localized table for the entity
        columns = [column.copy() for column in entity.table.c
                   if column.name in entity.__localized_fields__]

        entity_pks = entity._descriptor.primary_keys
        entity_pk_name = entity_pks[0].name
        # will voluntarily crash if entity has more than a single primary key
        if len(entity_pks) > 1:
            raise RuntimeError,  'Your entity *MUST* have a single primary key to be localized'
        columns.append(Column('translated_id', None,
                              ForeignKey("%s.%s" % (entity.table.name, entity_pk_name)),
                              primary_key=True,
                       ))


        entity_parent_class = entity_polymorph_class(entity)
        localized_parent_class = False
        if entity_parent_class:
            localized_parent_class = getattr(entity_parent_class, '__localized_class__', False)

        # if at root of the inheritance tree, add a translated_type column
        # to determine the type of object to load

        # XXX!!!! should find a way to determine if this is needed (non polymorph)

        if localized_parent_class:
            parent_table_name = localized_parent_class._sa_class_manager.mapper.mapped_table.name
            columns.append(Column('locale_id', None,
                                  ForeignKey('%s.locale_id' % parent_table_name),
                                  primary_key=True))
        else: # root case
            columns.append(Column('translated_type', Unicode(40), nullable=False))
            columns.append(Column('locale_id', Integer, primary_key=True))


        # now make the table
        table = Table(entity.table.name + '_localized', entity.table.metadata,
            *columns
        )
        entity.__localized_table__ = table


        # create a class to map to that table
        if localized_parent_class:
            Localized = type('Localized', (localized_parent_class, ),
                             {'__init__': localized_init, })
        else: # root case
            Localized = type('Localized', (object, ),
                             {'__init__': localized_init, })

        Localized.__name__ = entity.__name__ + 'Localized'
        Localized.__localized_entity__ = entity
        Localized.__not_localized_fields__ = [column.name for column in entity.table.c
                                           if not column.name in entity.__localized_fields__]

        # map the localized class to the localized table for this entity
#        mapper(Localized, table)


        if localized_parent_class:
            # if we inherit from another Localized
            mapper(Localized, table,
                   inherits=localized_parent_class,
                   polymorphic_identity='%s_localized' % entity.__name__.lower()
                   )
        else:
            # if at root of the inheritance tree, polymorphic_on is required
            mapper(Localized, table,
                   polymorphic_on=table.c.translated_type,
                   polymorphic_identity='%s_localized' % entity.__name__.lower()
                   )

        entity.__localized_class__ = Localized

        def get_localized_attr(self, attr):
            """ will return either the 'translated' attribute or
            the Localized one, as this will replace the __getattr__
            for the Localized class
            """
#
            if attr in Localized.__not_localized_fields__:
                return getattr(self.translated, attr)
            else:
                return self.__getattribute__(attr)


        # patching __getattr__ for Localized
        Localized.__getattr__ = get_localized_attr

    def after_mapper(self):
        """
        """
        entity = self.entity
        # we must name the relation after the entity name
        # otherwise it would supercede the same relationship on inherited mapper
        entity.mapper.add_property('%s_localized_versions' % entity.__name__,
                                   relation(entity.__localized_class__,
                                            backref='translated',
                                            )
                                   )

    def finalize(self):
        """ add helper methods to the entity
        """
        entity = self.entity

        def add_locale(self, locale_string, *args, **kw):
            """ adds a new language
            """
            localized = self.__localized_class__(translated_id=self.id)
            localized.locale_id = locale_string
            localized.__dict__.update(kw)
            getattr(self, '%s_localized_versions' % entity.__name__).append(localized)
            return localized

        def get_all_localized(self):
            """ returns translations for all languages excluding the default one
            """
            localized = getattr(self, '%s_localized_versions' % entity.__name__)
            return localized

        def get_many_localized(self, locale_strings):
            """ returns translations for a list of given language
            """
            localized = object_session(self).query(self.__localized_class__).filter(\
                   and_(self.__localized_class__.translated_id==self.id,
                        self.__localized_class__.locale_id.in_(locale_strings))).all()
            if self.default_locale in locale_strings:
                localized.append(self)
            return localized

        def get_localized(self, locale_string):
            """ return one and only one translation for a given language
            returns self if language is the default
            """
            if locale_string == self.default_locale:
                return self
            localized = None
            try:
                localized = object_session(self).query(self.__localized_class__).filter( \
                       and_(self.__localized_class__.translated_id==self.id,
                            self.__localized_class__.locale_id==locale_string))[0]
            except IndexError:
                pass
            return localized

        entity.add_locale = add_locale
        entity.get_all_localized = get_all_localized
        entity.get_many_localized = get_many_localized
        entity.get_localized = get_localized



acts_as_localized = Statement(LocalizedEntityBuilder)

