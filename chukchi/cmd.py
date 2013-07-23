import logging
import sys

def run():
    from chukchi.api import app
    print __file__
    print sys.modules['chukchi'].__file__
    logging.basicConfig(format="%(asctime)-15s %(name)s: %(message)s",
                        level=logging.DEBUG if app.debug else logging.INFO)
    app.run(*sys.argv[1:])

def init_db():
    from chukchi.db import engine
    from chukchi.db.models import Base

    Base.metadata.create_all(engine)

def update_feeds():
    from datetime import timedelta

    from sqlalchemy.orm import scoped_session

    from chukchi.config import config
    from chukchi.db import Session
    from chukchi.db.models import Feed
    from chukchi.feed.parse import update_feed
    from chukchi.utils import now

    logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO)

    LOG = logging.getLogger(__name__)

    db_search = Session()
    db_update = scoped_session(Session)

    if config.SOCKET_TIMEOUT:
        import socket
        socket.setdefaulttimeout(config.SOCKET_TIMEOUT)

    for feed in db_search.query(Feed).filter( Feed.active == True,
                                              Feed.retrieved_at <= (now() - timedelta(**config.UPDATE_DELAY)) ):
        feed_repr = repr(feed)
        try:
            db_search.expunge(feed)
            update_feed(db_update, feed=feed)
            db_update.commit()
        except Exception, e:
            LOG.exception("failure updating feed %s", feed_repr)
        db_update.remove()
