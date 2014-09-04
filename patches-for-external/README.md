patches
============================
Please do not apply these patches unless,
* You understand what they do.
* You understand how the license of the original software affects you if you
  do apply them.


web_socketio apache configuration
=================================

The server "python web_socketio/web_socketio/server.py -d mydb" must be run as
the same user as OpenERP.

Apache requires that the least specific URL be first. This is the opposite of
the documentation for web_socketio addon.

&lt;VirtualHost *:80&gt;
    ServerAdmin jssuzanne@anybox.fr
    ServerName www.myopenerp.fr
    &lt;location /&gt;
            ProxyPreserveHost On
            ProxyPass http://localhost:8069/
            ProxyPassReverse http://localhost:8069/
    &lt;/location&gt;
    &lt;location /socket.io&gt;
            ProxyPreserveHost On
            ProxyPass http://localhost:8068/socket.io
            ProxyPassReverse http://localhost:8068/socket.io
    &lt;/location&gt;
    &lt;location /socket.io/1/websocket&gt;
            ProxyPreserveHost On
            ProxyPass ws://localhost:8068/socket.io/1/websocket
            ProxyPassReverse ws://localhost:8068/socket.io/1/websocket
    &lt;/location&gt;

&lt;/VirtualHost&gt;


web_socketio and web_action_request are needed for pop-up on call
=================================================================
https://bitbucket.org/anybox/web_socketio/ (for 7.x use hg checkout default, not needed for 8.x/Odoo)
https://bitbucket.org/anybox/web_action_request/ (for 7.x use hg checkout 7.0, for 8.x/Odoo, use hg checkout 8.0)



WARNING WARNING WARNING
=======================

Do not just close windows/tabs/browser sessions. This will cause the web_socketio
server to consume resources (memory and CPU). Additionally, it starts losing pop-up requests.
Eventually, it just stops. Click to dial and caller id look-up continue to work.

ALWAYS LOG OUT PROPERLY!

Additionally, any time you restart OpenERP, you MUST restart the web_socketio
server. Restarting the proxy (apache or nginx) is a good idea.
