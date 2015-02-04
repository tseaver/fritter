
from crochet import setup, run_in_reactor
from pyramid.config import Configurator
from pyramid_zodbconn import get_connection
from .models import appmaker


def root_factory(request):
    conn = get_connection(request)
    return appmaker(conn.root())

@run_in_reactor
def start_ssh_server(port, username, password, namespace):
    """
    Start an SSH server on the given port, exposing a Python prompt with the
    given namespace.
    """
    # This is a lot of boilerplate, see http://tm.tl/6429 for a ticket to
    # provide a utility function that simplifies this.
    from twisted.internet import reactor
    from twisted.conch.insults import insults
    from twisted.conch import manhole, manhole_ssh
    from twisted.cred.checkers import (
        InMemoryUsernamePasswordDatabaseDontUse as MemoryDB)
    from twisted.cred.portal import Portal

    sshRealm = manhole_ssh.TerminalRealm()
    def chainedProtocolFactory():
        return insults.ServerProtocol(manhole.Manhole, namespace)
    sshRealm.chainedProtocolFactory = chainedProtocolFactory

    sshPortal = Portal(sshRealm, [MemoryDB(**{username: password})])
    reactor.listenTCP(port, manhole_ssh.ConchFactory(sshPortal),
                      interface="127.0.0.1")

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(root_factory=root_factory, settings=settings)
    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.scan()
    setup()
    app = config.make_wsgi_app()
    start_ssh_server(5022, "admin", "secret", {"app": app, 'config': config})
    return app
