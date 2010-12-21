from sqlalchemy            import Table, Column, and_, desc, ForeignKey
from sqlalchemy.orm        import mapper, MapperExtension, EXT_CONTINUE, \
                                  object_session, relation
from sqlalchemy            import ForeignKeyConstraint
from elixir                import Integer, DateTime
from elixir                import String
from elixir                import Unicode
from elixir.statements     import Statement
from elixir.properties     import EntityBuilder
from elixir.entity         import getmembers

from zope.interface import implementedBy, classImplements

from sqlalchemy.ext.associationproxy import association_proxy, \
                                    AssociationProxy


__all__ = ['acts_as_localized']
__doc_all__ = []


class LocalizedEntityBuilder(EntityBuilder):
    """ acts_as_localized statement
    """

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

        # create a localized table for the localized
        columns_and_constraints = [column.copy() for column in entity.table.c
                   if column.name in entity.__localized_fields__]

        entity_pks = entity._descriptor.primary_keys
        entity_pk_name = entity_pks[0].name
        # will voluntarily crash if entity has more than a single primary key
        if len(entity_pks) > 1:
            raise RuntimeError,  'Your entity *MUST* have a single primary key to be localized'

        # we define the primary key as a tuple (translated object, language)
        columns_and_constraints.append(Column('translated_id', None,
                              ForeignKey("%s.%s" % (entity.table.name, entity_pk_name)),
                              primary_key=True,
                       ))
        columns_and_constraints.append(Column('locale_id', String, primary_key=True))

        entity_parent_class = False
        for class_ in entity.__mro__[1:]:
            descriptor = getattr(class_, '_descriptor', False) # EntityBase has no _descriptor
            if descriptor and  getattr(class_._descriptor, 'table', None) is not None:
                entity_parent_class = class_

        localized_parent_class = False
        if entity_parent_class:
            localized_parent_class = getattr(entity_parent_class, '__localized_class__', False)

        # XXX!!!! should find a way to determine if this is needed (non polymorph)

        if localized_parent_class:
            # polymorphic inheritance is based on the foreign key tuple :
            # (translated content, language)
            # which tuple is the primary key of the root table
            parent_table_name = localized_parent_class._sa_class_manager.mapper.mapped_table.name
            columns_and_constraints.append(ForeignKeyConstraint(['translated_id',
                                                'locale_id'],
                                               ['%s.translated_id' % parent_table_name,
                                                '%s.locale_id' % parent_table_name]))
        else: # root case
            # if at root of the inheritance tree, add a translated_type column
            # to determine the type of object to load (polymorphic type)
            columns_and_constraints.append(Column('translated_type', Unicode(40), nullable=False))

        # now make the table
        table = Table(entity.table.name + '_localized', entity.table.metadata,
                      *columns_and_constraints
                     )

        entity.__localized_table__ = table

        not_localized_columns = [column.name for column in entity.table.c
                                   if not column.name in entity.__localized_fields__]

        # create a class to map to that table
        if localized_parent_class:
            not_localized_columns.extend(localized_parent_class.__not_localized_fields__)
            Localized = type('Localized', (localized_parent_class, ),
                             {'__init__': localized_init,
                              })
        else: # root case
            Localized = type('Localized', (object, ),
                             {'__init__': localized_init,
                              })
        # massage the object attributes
        # zope.interface implements declaration
        classImplements(Localized, implementedBy(entity))
        Localized.__not_localized_fields__ = not_localized_columns
        Localized.__name__ = entity.__name__ + 'Localized'
        Localized.__localized_entity__ = entity

        #  add assoc proxy for untranslated columns
        for fname in [field for field in not_localized_columns if not hasattr(Localized, field)]:
            setattr(Localized, fname, association_proxy('%s_translated' % Localized.__name__, fname))


        def localized__repr__(self):
            return '<%r %r, id: %r for: %r>' \
               % (self.__class__.__name__, self.locale_id,
                  self.translated_id, self.__localized_entity__)
        Localized.__repr__ = localized__repr__

        # map the localized class to the localized table for this entity
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



        def get_localized_attr(self, attr):
            """ will return either the 'translated' attribute or
            the Localized one, as this will replace the __getattr__
            for the Localized class
            """
#
#            if attr.startswith('gen'):
#                from nose.tools import set_trace; set_trace()

            if attr.startswith('_'):
                return object.__getattribute__(self, attr)
            try:
                return self.__getattribute__(attr)
            except AttributeError:
                translated = getattr(self, '%s_translated' % self.__class__.__name__)
                return getattr(translated, attr)

#            if attr in Localized.__not_localized_fields__:
#                translated = getattr(self, '%s_translated' % self.__class__.__name__)
#                return getattr(translated, attr)
#            else:
#                return self.__getattribute__(attr)

        # patching __getattr__ for Localized
        Localized.__getattr__ = get_localized_attr


        entity.__localized_class__ = Localized


    def after_mapper(self):
        """
        """
        entity = self.entity
        # we must name the relation after the entity name
        # otherwise it would supercede the same relationship on inherited mapper
        # same thing for the backref
        entity.mapper.add_property('%s_localized_versions' % entity.__name__,
                                   relation(entity.__localized_class__,
                                            backref='%s_translated' % entity.__localized_class__.__name__,
                                            cascade = 'all',
                                            )
                                   )


#    def create_properties(self):
#
#        entity = self.entity
#        # chercher ici les relations de entity pour les assoc proxyfier
#        tt=list(entity.mapper.iterate_properties)
#        from nose.tools import set_trace; set_trace()
##        zz=filter( lambda x: type(x) == type(RelationshipProperty), tt)

    def finalize(self):
        """ add helper methods to the entity
        """
        entity = self.entity

        def add_locale(self, locale_string, *args, **kw):
            """ add a new language
            """
            localized = self.__localized_class__(translated_id=self.id)
            localized.locale_id = locale_string
            localized.__dict__.update(kw)
            getattr(self, '%s_localized_versions' % entity.__name__).append(localized)
            return localized

        def edit_locale(self, locale_string, *args, **kw):
            """ edit a localized for a given language
            """
            localized = self.get_localized(locale_string)
            if localized is not None:
                localized.__dict__.update(kw)
            return localized

        def delete_locale(self, locale_string):
            """ delete a localized for a given language
            """
            localized = self.get_localized(locale_string)
            if localized is not self and localized is not None:
                object_session(self).delete(localized)

        def get_all_localized(self):
            """ returns translations for all languages *excluding* the default one
            """
            localized = getattr(self, '%s_localized_versions' % entity.__name__)
            return localized

        def get_many_localized(self, locale_strings):
            """ returns translations for a list of given language
            *including* default language if present in the list
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
            or None if translation is not set yet
            """
            localized = None
            try:
                localized = object_session(self).query(self.__localized_class__).filter( \
                       and_(self.__localized_class__.translated_id==self.id,
                            self.__localized_class__.locale_id==locale_string))[0]
            except IndexError:
                if locale_string == self.default_locale:
                    return self
                pass
            return localized

        entity.add_locale = add_locale
        entity.edit_locale = edit_locale
        entity.delete_locale = delete_locale
        entity.get_all_localized = get_all_localized
        entity.get_many_localized = get_many_localized
        entity.get_localized = get_localized



acts_as_localized = Statement(LocalizedEntityBuilder)

