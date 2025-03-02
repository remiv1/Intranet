function updateSousMenuEvent(idContract) {
    var contractId = idContract.getAttribute('data-event-id');
    var menu = document.getElementById('TypeE' + contractId).value;
    var sousmenu = document.getElementById('STypeE' + contractId);
    sousmenu.innerHTML = '';

    var options = []
    if (menu === 'Gestion') {
        var options = ['', 'Souscription', 'Gestion', 'Renégociation', 'Résiliation'];
    } else if (menu === 'Contact') {
        var options = ['', 'Appel', 'Mail', 'SMS'];
    } else if (menu === 'Contrat') {
        var options = ['', 'Contrat'];
    } else {
        var options = ['', 'Autre']
    }

    options.forEach(function(option) {
        var opt = document.createElement('option');
        opt.innerHTML = option;
        sousmenu.appendChild(opt);
    });
}

function updateSousMenuDocument(idContract) {
    var contractId = idContract.getAttribute('data-event-id');
    var menu = document.getElementById('TypeD' + contractId).value;
    var sousmenu = document.getElementById('STypeD' + contractId);
    sousmenu.innerHTML = '';

    var options = []
    if (menu === 'Contact') {
        var options = ['', 'Appel', 'Mail', 'SMS'];
    } else if (menu === 'Contrat') {
        var options = ['', 'Contrat', 'Avenant', 'Résiliation'];
    } else {
        var options = ['', 'Autre']
    }

    options.forEach(function(option) {
        var opt = document.createElement('option');
        opt.innerHTML = option;
        sousmenu.appendChild(opt);
    });
}

$(document).ready(function() {
    $('.collapse').on('shown.bs.collapse', function() {
        $(this).parent().find(".fas").removeClass("fa-chevron-down").addClass("fa-chevron-up");
    }).on('hidden.bs.collapse', function() {
        $(this).parent().find(".fas").removeClass("fa-chevron-up").addClass("fa-chevron-down");
    });
});
