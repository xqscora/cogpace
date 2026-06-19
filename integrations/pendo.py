"""Pendo SDK integration for CogPace (Streamlit).

Injects the Pendo install snippet and anonymous initialization into the
parent frame via ``st.components.v1.html``.  A guard flag on the parent
window ensures the snippet and ``pendo.initialize`` execute only once per
page load, even though Streamlit re-runs the script on every interaction.
"""

import streamlit.components.v1 as components

PENDO_SNIPPET = """
<script>
if (!window.parent.__pendo_injected) {
    window.parent.__pendo_injected = true;

    (function(apiKey){
        (function(p,e,n,d,o){var v,w,x,y,z;o=p[d]=p[d]||{};o._q=o._q||[];
        v=['initialize','identify','updateOptions','pageLoad','track','trackAgent'];for(w=0,x=v.length;w<x;++w)(function(m){
        o[m]=o[m]||function(){o._q[m===v[0]?'unshift':'push']([m].concat([].slice.call(arguments,0)));};})(v[w]);
        y=e.createElement(n);y.async=!0;y.src='https://cdn.pendo.io/agent/static/'+apiKey+'/pendo.js';
        z=e.getElementsByTagName(n)[0];z.parentNode.insertBefore(y,z);})(window.parent,window.parent.document,'script','pendo');
    })('090a5cd3-c454-4928-ad9f-e9dcded1a917');

    window.parent.pendo.initialize({
        visitor: { id: '' }
    });
}
</script>
"""


def inject_pendo() -> None:
    """Inject the Pendo SDK into the Streamlit app (idempotent)."""
    components.html(PENDO_SNIPPET, height=0, width=0)
