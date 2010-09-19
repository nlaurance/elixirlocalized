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

    using_options(tablename='media')
    acts_as_localized(for_fields=['title', 'content'], default_locale='en')

class Movie(Media):
    has_field('resume', Unicode)

    using_options(inheritance='multi', polymorphic=True, tablename='movie')
    acts_as_localized(for_fields=['resume'], default_locale='en')


class TestPolymorphLocalized(unittest.TestCase):

    def setUp(self):
        """Method used to build a database"""
        metadata.bind = engine
        setup_all()
        create_all()

        movie = Movie(author='unknown', title='A Thousand and one nights',
                           content='It has been related to me, O happy King, said Shahrazad',
                           resume='not suitable for young children')
        session.add(movie)
        session.commit()
        session.expunge_all()

    def tearDown(self):
        """Method used to destroy a database"""
#        session.rollback()
#        drop_all()


    @do_it
    def test_get_localized_versions(self):
        # media attribute
        retrieved_movie = Movie.get(1)
        fr = retrieved_movie.add_locale('fr', title='Les mille et une nuits',
                                   content=u"J'ai entendu dire, Ô mon roi, dit Scheherazade",
                                   resume=u'déconseillé aux jeune public')
        session.commit()
        session.expunge_all()

        retrieved_movie = Movie.query.one()
        assert retrieved_movie.get_localized('fr').title == 'Les mille et une nuits'
        # movie attribute
        assert retrieved_movie.get_localized('fr').resume == u'déconseillé aux jeune public'
