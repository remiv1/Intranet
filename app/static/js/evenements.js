function updateSousMenuEvent(idContract) {
    let contractId = idContract.getAttribute('data-event-id');
    let menu = document.getElementById('TypeE' + contractId).value;
    let sousmenu = document.getElementById('STypeE' + contractId);
    let currentValue = sousmenu.value;
    sousmenu.innerHTML = '';

    let options = []
    if (menu === 'Gestion') {
        options = ['', 'Souscription', 'Gestion', 'Renégociation', 'Résiliation', 'Autre'];
    } else if (menu === 'Contact') {
        options = ['', 'Appel', 'Mail', 'SMS', 'Courrier'];
    } else if (menu === 'Contrat') {
        options = ['', 'Contrat'];
    } else {
        options = ['', 'Autre']
    }

    options.forEach(function(option) {
        let opt = document.createElement('option');
        opt.value = option;
        opt.innerHTML = option;
        // Restaurer la sélection si elle correspond à une option valide
        if (option === currentValue) {
            opt.selected = true;
        }
        sousmenu.appendChild(opt);
    });
}

function updateSousMenuDocument(idContract) {
    let contractId = idContract.getAttribute('data-event-id');
    let menu = document.getElementById('TypeD' + contractId).value;
    let sousmenu = document.getElementById('STypeD' + contractId);
    let currentValue = sousmenu.value;
    sousmenu.innerHTML = '';

    let options = []
    if (menu === 'Contact') {
        options = ['', 'Appel', 'Mail', 'SMS', 'Courrier'];
    } else if (menu === 'Contrat') {
        options = ['', 'Contrat', 'Avenant', 'Résiliation', 'Autre'];
    } else {
        options = ['', 'Autre']
    }

    options.forEach(function(option) {
        let opt = document.createElement('option');
        opt.value = option;
        opt.innerHTML = option;
        // Restaurer la sélection si elle correspond à une option valide
        if (option === currentValue) {
            opt.selected = true;
        }
        sousmenu.appendChild(opt);
    });
}

function openTab(evt, tabName) {
    let i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    // Masquer tous les contenus de tab
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].classList.remove("d-block");
        tabcontent[i].classList.add("d-none");
    }
    // Désactiver tous les onglets
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    // Afficher le contenu du tab sélectionné
    document.getElementById(tabName).classList.remove('d-none');
    document.getElementById(tabName).classList.add('d-block');
    // Activer l'onglet sélectionné
    evt.currentTarget.className += " active";
}