function updateSousMenu(idContract) {
    let contractId = idContract.getAttribute('data-contract-id');
    let menu = document.getElementById('Type' + contractId).value;
    let sousmenu = document.getElementById('SType' + contractId);
    sousmenu.innerHTML = '';

    let options = []
    if (menu === 'Finance') {
        options = ['', 'Banque', 'Assurances', 'Autre'];
    } else if (menu === 'Juridique') {
        options = ['', 'Conseils', 'Comptabilité', 'Autre'];
    } else if (menu === 'RH') {
        options = ['', 'Titulaires', 'Bénévoles', 'Autre'];
    } else if (menu === 'Materiel') {
        options = ['', 'Immobilier', 'Matériel durable', 'Matériel consomptible', 'Informatique', 'Autre']
    } else if (menu === 'Services') {
        options = ['', 'Prestations régulières', 'Prestations à la demande', 'Autre']
    } else {
        options = ['', 'Autre']
    }

    options.forEach(function(option) {
        let opt = document.createElement('option');
        opt.innerHTML = option;
        sousmenu.appendChild(opt);
    });
}

function updateSousFiltre() {
    let menu = document.getElementById('TypeFiltre').value;
    let sousmenu = document.getElementById('STypeFiltre');
    sousmenu.innerHTML = '';

    let options = []
    if (menu === 'Finance') {
        options = ['', 'Banque', 'Assurances', 'Autre'];
    } else if (menu === 'Juridique') {
        options = ['', 'Conseils', 'Comptabilité', 'Autre'];
    } else if (menu === 'RH') {
        options = ['', 'Titulaires', 'Bénévoles', 'Autre'];
    } else if (menu === 'Materiel') {
        options = ['', 'Immobilier', 'Matériel durable', 'Matériel consomptible', 'Informatique', 'Autre']
    } else if (menu === 'Services') {
        options = ['', 'Prestations régulières', 'Prestations à la demande', 'Autre']
    } else {
        options = ['', 'Autre']
    }

    options.forEach(function(option) {
        let opt = document.createElement('option');
        opt.innerHTML = option;
        sousmenu.appendChild(opt);
    });

    sousmenu.disabled = false;
}

$(document).ready(function() {
    $('.collapse').on('shown.bs.collapse', function() {
        $(this).parent().find(".fas").removeClass("fa-chevron-down").addClass("fa-chevron-up");
    }).on('hidden.bs.collapse', function() {
        $(this).parent().find(".fas").removeClass("fa-chevron-up").addClass("fa-chevron-down");
    });
});

function filterTable(event) {
    event.preventDefault();
    
    let typeFiltre = document.getElementById('TypeFiltre').value;
    let subTypeFiltre = document.getElementById('STypeFiltre').value;
    let rows = document.querySelectorAll('#contractsTable tbody tr');
    
    rows.forEach(function(row) {
        let type = row.getAttribute('data-type');
        let subtype = row.getAttribute('data-stype');

        if ((typeFiltre === "" || type === typeFiltre) && (subTypeFiltre === "" || subtype === subTypeFiltre)) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
}