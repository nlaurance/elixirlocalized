# -*- coding: utf-8 -*-
from elixir import has_field, Unicode, Date, using_options
from elixir import Entity
from elixirext.localized import acts_as_localized

from elixir import setup_all, create_all, drop_all, cleanup_all

from elixir import metadata, session
from sqlalchemy.test.testing import assert_raises
import unittest
from tests import engine, do_it

class Media(Entity):
    has_field('author', Unicode)
    has_field('title', Unicode)
    has_field('content', Unicode)

    acts_as_localized(for_fields=['title', 'content'], default_locale='en')
    using_options(inheritance='multi', polymorphic=True, tablename='media')

class Movie(Media):
    has_field('resume', Unicode)

    acts_as_localized(for_fields=['resume'], default_locale='en')
    using_options(inheritance='multi', polymorphic=True, tablename='movie')


class TestPolymorphLocalized(unittest.TestCase):

    def setUp(self):
        """Method used to build a database"""
        metadata.bind = engine
        setup_all()
        create_all()

        self.movie = Movie(author='unknown', title='A Thousand and one nights',
                           content='It has been related to me, O happy King, said Shahrazad',
                           resume='not suitable for young children')
        session.add(self.movie)
        session.commit()

    def tearDown(self):
        """Method used to destroy a database"""
        session.rollback()
        drop_all()

    def test_localized_versions(self):
        fr = self.movie.add_locale('fr', title='Les mille et une nuits',
                                   content=u"J'ai entendu dire, Ô mon roi, dit Scheherazade",
                                   resume=u'déconseillé aux jeune public')
        session.commit()
        # media attribute
        assert self.movie.get_localized('fr').title == 'Les mille et une nuits'
        # movie attribute
        assert self.movie.get_localized('fr').resume == u'déconseillé aux jeune public'
