(function() {
    window.addEventListener("load", init);

    function init() {
        if (!hasCookieSet()) {
            console.log('cookie not exists yet, showing consent form');
            document.getElementById('consent_form').classList.remove('hidden');
            document.getElementById('main_content').classList.add('hidden');
            let form = document.querySelector('form');
            form.addEventListener('submit', setConsentCookie);
        } else {
            if (hasCookieTrue()) {
                console.log('user has given consent');
            } else {
                console.log('user has not given consent');
            }
        }
    }

    function hasCookieSet() {
        return document.cookie.split(';').some((item) => item.trim().startsWith('spritesconsent='));
    }

    function hasCookieTrue() {
        return document.cookie.split(';').some((item) => item.includes('spritesconsent=true'));
    }

    function setConsentCookie(e) {
        if (!document.querySelector('input[name="consent-option"]:checked')) {
            console.log('submit without choosing')
            document.getElementById('submit-warning').className = '';
            e.preventDefault();
        } else {
            document.cookie = "spritesconsent=" + document.querySelector('input[name="consent-option"]:checked').value;
        }
        // delete cookie: document.cookie="spritesconsent= ; expires=Thu, 01 Jan 1970 00:00:01 GMT"
    }
})();