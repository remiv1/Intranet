function updateSousMenuEvent(idContract) {
    var contractId = idContract.getAttribute('data-event-id');
    var menu = document.getElementById('TypeE' + contractId).value;
    var sousmenu = document.getElementById('STypeE' + contractId);
    sousmenu.innerHTML = '';

    var options = []
    if (menu === 'Gestion') {
        var options = ['', 'Souscription', 'Gestion', 'Renégociation', 'Résiliation', 'Autre'];
    } else if (menu === 'Contact') {
        var options = ['', 'Appel', 'Mail', 'SMS', 'Courrier'];
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
        var options = ['', 'Appel', 'Mail', 'SMS', 'Courrier'];
    } else if (menu === 'Contrat') {
        var options = ['', 'Contrat', 'Avenant', 'Résiliation', 'Autre'];
    } else {
        var options = ['', 'Autre']
    }

    options.forEach(function(option) {
        var opt = document.createElement('option');
        opt.innerHTML = option;
        sousmenu.appendChild(opt);
    });
}

function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
      tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}