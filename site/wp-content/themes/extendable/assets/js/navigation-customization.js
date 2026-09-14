(function () {
    'use strict';

    function injectSiteLogoTitle() {
        const container = document.querySelector('.wp-block-navigation__responsive-dialog');
        if (!container) return;

        if (container.querySelector('.site-logo-title')) return;

        if (!window.ExtendableNavData) return;

        const { logoUrl, siteTitle } = window.ExtendableNavData;
        const hasSiteTitle = !!document.querySelector('header.wp-block-template-part .wp-block-site-title');

        const wrapper = document.createElement('div');
        wrapper.className = 'site-logo-title wp-block-site-logo';
        wrapper.innerHTML = `
            ${logoUrl ? `<img src="${logoUrl}" alt="Site Logo" class="mobile-logo" />` : ''}
            ${hasSiteTitle ? `<span class="site-title">${siteTitle || ''}</span>` : ''}
        `;
        container.prepend(wrapper);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectSiteLogoTitle);
    } else {
        injectSiteLogoTitle();
    }
})();

/*
 * Menu header (hamburger + pannello a schermo intero): implementazione
 * propria, senza dipendenze. Il pulsante/tendina originali del tema
 * dipendevano dalla Interactivity API di WordPress (@wordpress/interactivity),
 * risolta tramite un importmap che punta pero' a un URL assoluto sul dominio
 * di produzione: nelle anteprime su un altro dominio quell'import fallisce e
 * il toggle non funziona mai, su nessuna dimensione di schermo.
 * Vedi tools/fix_header_nav.py.
 */
(function () {
    'use strict';

    function initCipNav() {
        var toggle = document.querySelector('.cip-nav-toggle');
        var panel = document.getElementById('cip-nav-panel');
        if (!toggle || !panel) return;
        var closeBtn = panel.querySelector('.cip-nav-panel-close');

        function openPanel() {
            panel.hidden = false;
            document.body.style.overflow = 'hidden';
            toggle.setAttribute('aria-expanded', 'true');
            var firstLink = panel.querySelector('a');
            if (firstLink) firstLink.focus();
        }
        function closePanel() {
            panel.hidden = true;
            document.body.style.overflow = '';
            toggle.setAttribute('aria-expanded', 'false');
            toggle.focus();
        }
        toggle.addEventListener('click', function () {
            if (panel.hidden) openPanel(); else closePanel();
        });
        if (closeBtn) closeBtn.addEventListener('click', closePanel);
        panel.addEventListener('click', function (e) {
            if (e.target === panel) closePanel();
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && !panel.hidden) closePanel();
        });
        window.addEventListener('resize', function () {
            if (window.innerWidth >= 783 && !panel.hidden) closePanel();
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCipNav);
    } else {
        initCipNav();
    }
})();