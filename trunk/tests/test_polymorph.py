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


    def tearDown(self):
        """Method used to destroy a database"""
        session.rollback()
        drop_all()

    def test_get_localized_versions(self):
        movie = Movie(author='unknown', title='A Thousand and one nights',
                           content='It has been related to me, O happy King, said Shahrazad',
                           resume='not suitable for young children')
        session.add(movie)
        session.commit()
        session.expunge_all()
        # media attribute
        retrieved_movie = Movie.get(1)
        fr = retrieved_movie.add_locale('fr', title='Les mille et une nuits',
                                   content=u"J'ai entendu dire, Ô mon roi, dit Scheherazade",
                                   resume=u'déconseillé au jeune public')
        session.commit()
        session.expunge_all()

        retrieved_movie = Movie.query.one()
        assert retrieved_movie.get_localized('fr').title == 'Les mille et une nuits'
        # movie attribute
        assert retrieved_movie.get_localized('fr').resume == u'déconseillé au jeune public'

    def test_create_other_default(self):
        movie = Movie(author='Proust', title=u'À la recherche du temps perdu',
                           content=u'Longtemps, je me suis couché de bonne heure.',
                           resume=u'Du côté de chez Swann',
                           default_locale = "fr")
        movie.add_locale('en', title=u'In Search of Lost Time and Remembrance of Things Past',
                                   content=u"For a long time I used to go to bed early.",
                                   resume=u'translated into English by C. K. Scott Moncrieff')
        session.flush()
        movie = Movie(author='disney',title=u'الأشرار الصغار وألعابهم الجميلة',
                     content=u"يستمتع الكبار قبل الصغار (او بنفس الدرجة على الأقل) بكل فيلم من سلسلة 'توي ستوري' يظهر في",
                     resume=u'ومكتوبة بالتوازن الدقيق الذي',
                     default_locale = 'ar')
        movie.add_locale('en', title=u'Toy Story',
                                   content=u"woody & friends.",
                                   resume=u'a nice cartoon')
        session.commit()
        session.expunge_all()
#        Movie.__localized_class__.localquery()
#        from nose.tools import set_trace; set_trace()
        retrieved_movie = Movie.query.first()
        assert retrieved_movie.get_localized('fr').title == u'À la recherche du temps perdu'
        assert retrieved_movie.get_localized('en').title == 'In Search of Lost Time and Remembrance of Things Past'