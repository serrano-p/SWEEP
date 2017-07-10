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

monitor = new Ajax.PeriodicalUpdater('posts','/sweep', {
      method: 'get',
      frequency: 1,
      decay: 1.1,
      onFailure: function() {'<p>SWEEP HS</p>' }
    });
monitor.stop();

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
    monitoring();
}

function end() {}

function monitoring() {
    monitor.start()
}

function bestof() {
    monitor.stop()
    $('posts').update('<p>Best Of is computing. Please waiting.</p>');
    new Ajax.Request('/bestof', {
        method: 'get',
        onSuccess: function (trs) {
            bo = trs.responseText
            $('posts').hide();
            $('posts').update(bo);
            $('posts').appear();
        },
        onFailure: function () {
            alert('apropos: Impossible d\'obtenir la rubrique !')
        }
    });
}

function aides() {
    monitor.stop()
    if (messages_aides == null) {
        // new Ajax.Request('/mentions', {
        //     method: 'get',
        //     onSuccess: function (trs) {
        //         messages_mentions = trs.responseText
        //         $('posts').hide();
        //         $('posts').update(messages_mentions);
        //         $('posts').appear();
        //     },
        //     onFailure: function () {
        //         alert('mentions: Impossible d\'obtenir la rubrique !')
        //     }
        // });
        messages_aides = '<div class="post"><h2 class="title">Icônes utilisés</h2><div class="story">';
        messages_aides = messages_aides
                +'<p><img src="./static/images/home_64.png" width="32" alt="aide"/> : permet de consulter le monitoring.</p>'
                +'<p><img src="./static/images/help_64.png" width="32" alt="aide"/> : permet de consulter cette aide.</p>'
                +'<p><img src="./static/images/briefcase_64.png" width="32" alt="Best Of !"/> : permet de consulter les requêtes les plus fréquentes.</p>'
                +'<p><img src="./static/images/info_64.png" width="32" alt="base de données"/> : propose quelques informations.</p>'
                +'<p><img src="./static/images/shield_64.png" width="32" alt="base de données"/> : Énonce les différentes mentions légales liées à cette application.</p>'
                ;
        messages_aides = messages_aides+ '</div></div>';
    } else {
        $('posts').hide();
        $('posts').update(messages_aides);
        $('posts').appear();
    }
}

function mentions() {
    // if (messages_mentions == null) {
    //     new Ajax.Request('/mentions', {
    //         method: 'get',
    //         onSuccess: function (trs) {
    //             messages_mentions = trs.responseText
    //             $('posts').hide();
    //             $('posts').update(messages_mentions);
    //             $('posts').appear();
    //         },
    //         onFailure: function () {
    //             alert('mentions: Impossible d\'obtenir la rubrique !')
    //         }
    //     });
    // } else {
    //     messages_mentions = '<div class="post"><h2 class="title">Mentions</h2> <h3 class="posted">par E. Desmontils</h3><div class="story">' 
    //                         + messages_mentions + "</div></div>\n";
    //     $('posts').hide();
    //     $('posts').update(messages_mentions);
    //     $('posts').appear();
    // }
}

function apropos() {
    // if (messages_apropos == null) {
    //     new Ajax.Request('/apropos', {
    //         method: 'get',
    //         onSuccess: function (trs) {
    //             messages_apropos = trs.responseText
    //             $('posts').hide();
    //             $('posts').update(messages_apropos);
    //             $('posts').appear();
    //         },
    //         onFailure: function () {
    //             alert('apropos: Impossible d\'obtenir la rubrique !')
    //         }
    //     });
    // } else {
    //     $('posts').hide();
    //     $('posts').update(messages_apropos);
    //     $('posts').appear();
    // }
}
//</script>