function updateSousMenu(idContract) {
    var contractId = idContract.getAttribute('data-contract-id');
    var menu = document.getElementById('Type' + contractId).value;
    var sousmenu = document.getElementById('SType' + contractId);
    sousmenu.innerHTML = '';

    var options = []
    if (menu === 'Finance') {
        var options = ['', 'Banque', 'Assurances', 'Autre'];
    } else if (menu === 'Juridique') {
        var options = ['', 'Conseils', 'Comptabilité', 'Autre'];
    } else if (menu === 'RH') {
        var options = ['', 'Titulaires', 'Bénévoles', 'Autre'];
    } else if (menu === 'Materiel') {
        var options = ['', 'Immobilier', 'Matériel durable', 'Matériel consomptible', 'Informatique', 'Autre']
    } else if (menu === 'Services') {
        var options = ['', 'Prestations régulières', 'Prestations à la demande', 'Autre']
    } else {
        var options = ['', 'Autre']
    }

    options.forEach(function(option) {
        var opt = document.createElement('option');
        opt.innerHTML = option;
        sousmenu.appendChild(opt);
    });
}

function updateSousFiltre() {
    var menu = document.getElementById('TypeFiltre').value;
    var sousmenu = document.getElementById('STypeFiltre');
    sousmenu.innerHTML = '';

    var options = []
    if (menu === 'Finance') {
        var options = ['', 'Banque', 'Assurances', 'Autre'];
    } else if (menu === 'Juridique') {
        var options = ['', 'Conseils', 'Comptabilité', 'Autre'];
    } else if (menu === 'RH') {
        var options = ['', 'Titulaires', 'Bénévoles', 'Autre'];
    } else if (menu === 'Materiel') {
        var options = ['', 'Immobilier', 'Matériel durable', 'Matériel consomptible', 'Informatique', 'Autre']
    } else if (menu === 'Services') {
        var options = ['', 'Prestations régulières', 'Prestations à la demande', 'Autre']
    } else {
        var options = ['', 'Autre']
    }

    options.forEach(function(option) {
        var opt = document.createElement('option');
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
    
    var typeFiltre = document.getElementById('TypeFiltre').value;
    var subTypeFiltre = document.getElementById('STypeFiltre').value;
    var rows = document.querySelectorAll('#contractsTable tbody tr');
    
    rows.forEach(function(row) {
        var type = row.getAttribute('data-type');
        var subtype = row.getAttribute('data-stype');

        if ((typeFiltre === "" || type === typeFiltre) && (subTypeFiltre === "" || subtype === subTypeFiltre)) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
}