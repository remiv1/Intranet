// Appeler la fonction au chargement de la page
document.addEventListener('DOMContentLoaded', updateTypeDocs);

// Récupération des données de typages et mise à jour des menus
function updateTypeDocs() {
    const typeMenus = Object.keys(menusData);
    const typeFiltre = document.getElementById('TypeFiltre');
    const typeModalAjout = document.getElementById('Type0');
    // Sélectionner toutes les modales de modifications (id commençant par 'Type' + id_contrat > 0)
    const modalsModification = Array.from(document.querySelectorAll('[id^="Type"]'))
        .filter(el => {
            const id = el.id.replace('Type', '');
            return /^\d+$/.test(id) && Number(id) > 0;
        });

    // Création des options de Type de contrat dans les menus déroulants de filtres
    if (typeFiltre) {
        typeFiltre.innerHTML = '';
        typeMenus.forEach(function(type) {
            let opt = document.createElement('option');
            opt.value = type;
            opt.innerHTML = type;
            typeFiltre.appendChild(opt);
        });
    }

    // Création des options de Type de contrat dans les menus déroulants des modals de modification
    if (typeModalAjout) {
        typeModalAjout.innerHTML = '';
        typeMenus.forEach(function(type) {
            let opt = document.createElement('option');
            opt.value = type;
            opt.innerHTML = type;
            typeModalAjout.appendChild(opt);
        });
    }

    if (modalsModification.length > 0) {
        modalsModification.forEach(function(modalType) {
            modalType.innerHTML = '';
            typeMenus.forEach(function(type) {
                let opt = document.createElement('option');
                opt.value = type;
                opt.innerHTML = type;
                // Restaurer la sélection si elle correspond à une option valide
                if (type === modalType.getAttribute('data-contract-value')) {
                    opt.selected = true;
                }
                modalType.appendChild(opt);
            });
        });
    }
}

function updateSousMenu(idContract) {
    let contractId = idContract.getAttribute('data-contract-id');
    let currentValue = idContract.getAttribute('data-s-type-value');
    let menu = document.getElementById('Type' + contractId).value;
    let sousmenu = document.getElementById('SType' + contractId);
    sousmenu.innerHTML = '';

    // Utilisation des données passées depuis le json en backend
    let options = menusData[menu] || menusData['Autre'];

    options.forEach(function(option) {
        let opt = document.createElement('option');
        opt.value = option;
        // Restaurer la sélection si elle correspond à une option valide
        if (option === currentValue) {
            opt.selected = true;
        }
        opt.innerHTML = option;
        sousmenu.appendChild(opt);
    });
}

function updateSousFiltre() {
    let menu = document.getElementById('TypeFiltre').value;
    let sousmenu = document.getElementById('STypeFiltre');
    sousmenu.innerHTML = '';

    // Utilisation des données passées depuis le json en backend
    let options = menusData[menu] || menusData['Autre'];

    options.forEach(function(option) {
        let opt = document.createElement('option');
        opt.innerHTML = option;
        sousmenu.appendChild(opt);
    });

    sousmenu.disabled = false;
}

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