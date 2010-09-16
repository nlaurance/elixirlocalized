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

    def after_mapper(self):
        entity = self.entity
        # we must name the relation after the entity name
        # otherwise it would supercede the same relationship on inherited mapper
        entity.mapper.add_property('%s_localized_versions' % entity.__name__,
                                   relation(entity.__localized_class__, backref='parent'))

    # we copy columns from the main entity table, so we need it to exist first
    def after_table(self):

        # create an object that represents a local for the entity
        class Localized(object):
            def __init__(self, **kw):
                self.__dict__.update(kw)

        entity = self.entity

        # create a localized table for the entity
        columns = [column.copy() for column in entity.table.c
                   if column.name in entity.__localized_fields__]
        columns.append(Column('locale_id', Integer, primary_key=True))

        entity_pks = entity._descriptor.primary_keys
        entity_pk_name = entity_pks[0].name
        # will voluntarily crash if entity has more than a single primary key
        if len(entity_pks) > 1:
            raise RuntimeError,  'Your entity *MUST* have a single primary key to be localized'
        columns.append(Column('parent_id', Integer,
                              ForeignKey("%s.%s" % (entity.table.name, entity_pk_name)),
                              primary_key=True,
                       ))

        # now make the table
        table = Table(entity.table.name + '_localized', entity.table.metadata,
            *columns
        )
        entity.__localized_table__ = table

        # map the localized class to the localized table for this entity
        Localized.__name__ = entity.__name__ + 'Localized'
        Localized.__localized_entity__ = entity
        Localized.__not_localized_fields__ = [column.name for column in entity.table.c
                                           if not column.name in entity.__localized_fields__]
        mapper(Localized, entity.__localized_table__)
        entity.__localized_class__ = Localized

        def get_localized_attr(self, attr):
            """ will return either the 'parent' attribute or
            the Localized one, as this will replace the __getattr__
            for the Localized class
            """

            if attr in Localized.__not_localized_fields__:
                return getattr(self.parent, attr)
            else:
                return self.__getattribute__(attr)

        # patching __getattr__ for Localized
        Localized.__getattr__ = get_localized_attr

        # helper methods
        def add_locale(self, locale_string, *args, **kw):
            """ adds a new language
            """
            localized = Localized(parent_id=self.id)
            localized.locale_id = locale_string
            localized.__dict__.update(kw)
            getattr(self, '%s_localized_versions' % entity.__name__).append(localized)
            return localized

        def get_all_localized(self):
            """ returns translations for all languages including the default one
            """
            localized = getattr(self, '%s_localized_versions' % entity.__name__)
            localized.append(self)
            return localized

        def get_many_localized(self, locale_strings):
            """ returns translations for a list of given language
            """
            localized = object_session(self).query(Localized).filter(\
                   and_(Localized.parent_id==self.id,
                        Localized.locale_id.in_(locale_strings))).all()
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
                localized = object_session(self).query(Localized).filter( \
                       and_(Localized.parent_id==self.id,
                            Localized.locale_id==locale_string))[0]
            except IndexError:
                pass
            return localized

        entity.add_locale = add_locale
        entity.get_all_localized = get_all_localized
        entity.get_many_localized = get_many_localized
        entity.get_localized = get_localized

acts_as_localized = Statement(LocalizedEntityBuilder)

