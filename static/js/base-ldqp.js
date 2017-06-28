//<script language="javascript">
// nécessite Prototypejs.org et Script.aculo.us


//=================================================================
// Contrôle de la sortie de page pour éviter de perdre les requêtes
//=================================================================

window.onbeforeunload = function (evt) {
    var message = '';
    if (typeof evt == 'undefined') {
        evt = window.event;
    }
    if (evt) {
        evt.returnValue = message;
    }
    return message;
}

//=======================================================
// Fonctions de gestion de l'interface et des appels AJAX
//=======================================================

function clear() {	
    // mémorisation des messages et aides pour éviter de charger le serveur.
    messages_aides = null;
    messages = null;
    messages_mentions = null;
    messages_apropos = null;

	// Page effacée
    $('posts').update("");
}

function init() {
    clear();
    news();
}

function end() {

}

function news() {
    new Ajax.PeriodicalUpdater('posts','/lift', {
      method: 'get',
      frequency: 4,
      decay: 1
    });
}

//</script>