// Appeler les fonctions de mise à jour des menus déroulants de typage au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    updateTypeEvenements(menusEvents);
    updateTypeDocuments(menusDocuments);
});

// Récupération des données de typages d'évènement et mise à jour des menus
function updateTypeEvenements(menusEvents) {
    const typeMenus = Object.keys(menusEvents);
    const typeModalAjoutEvenement = document.getElementById('TypeE0');
    // Sélectionner toutes les modales de modifications (id commençant par 'TypeE' + id_contrat > 0)
    const typeModalModifEvenement = Array.from(document.querySelectorAll('[id^="TypeE"]'))
        .filter(el => {
            const id = el.id.replace('TypeE', '');
            return /^\d+$/.test(id) && Number(id) > 0;
        });


    if (typeModalAjoutEvenement) {
        typeModalAjoutEvenement.innerHTML = '';
        typeMenus.forEach(function(type) {
            let opt = document.createElement('option');
            opt.value = type;
            opt.innerHTML = type;
            typeModalAjoutEvenement.appendChild(opt);
        });
    }

    if (typeModalModifEvenement.length > 0) {
        typeModalModifEvenement.forEach(function(modalType) {
            modalType.innerHTML = '';
            typeMenus.forEach(function(type) {
                let opt = document.createElement('option');
                opt.value = type;
                opt.innerHTML = type;
                // Restaurer la sélection si elle correspond à une option valide
                if (type === modalType.getAttribute('data-event-type-value')) {
                    opt.selected = true;
                }
                modalType.appendChild(opt);
            });
        });
    }
}

// Récupération des données de typages de document et mise à jour des menus
function updateTypeDocuments(menusDocuments) {
    const typeMenus = Object.keys(menusDocuments);
    const typeModalAjoutDocument = document.getElementById('TypeD0');
    // Sélectionner toutes les modales de modifications (id commençant par 'TypeD' + id_contrat > 0)
    const typeModalModifDocument = Array.from(document.querySelectorAll('[id^="TypeD"]'))
        .filter(el => {
            const id = el.id.replace('TypeD', '');
            return /^\d+$/.test(id) && Number(id) > 0;
        });
    if (typeModalAjoutDocument) {
        typeModalAjoutDocument.innerHTML = '';
        typeMenus.forEach(function(type) {
            let opt = document.createElement('option');
            opt.value = type;
            opt.innerHTML = type;
            typeModalAjoutDocument.appendChild(opt);
        });
    }
    if (typeModalModifDocument.length > 0) {
        typeModalModifDocument.forEach(function(modalType) {
            modalType.innerHTML = '';
            typeMenus.forEach(function(type) {
                let opt = document.createElement('option');
                opt.value = type;
                opt.innerHTML = type;
                // Restaurer la sélection si elle correspond à une option valide
                if (type === modalType.getAttribute('data-document-type-value')) {
                    opt.selected = true;
                }
                modalType.appendChild(opt);
            });
        });
    }
}

// Fonction de mise à jour des sous-menus en fonction du type sélectionné (Evènements)
function updateSousMenuEvent(idContract, menuEvents) {
    let eventID = idContract.getAttribute('data-event-id');
    let menu = document.getElementById('TypeE' + eventID).value;
    let sousmenu = document.getElementById('STypeE' + eventID);
    let currentValue = idContract.getAttribute('data-stype-event-value');
    sousmenu.innerHTML = '';

    // Utilisation des données passées depuis le json en backend
    let options = menuEvents[menu] || menuEvents['Autre'];

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

// Fonction de mise à jour des sous-menus en fonction du type sélectionné (Documents)
function updateSousMenuDocument(idContract, menuDocuments) {
    let documentID = idContract.getAttribute('data-document-id');
    let menu = document.getElementById('TypeD' + documentID).value;
    let sousmenu = document.getElementById('STypeD' + documentID);
    let currentValue = idContract.getAttribute('data-stype-document-value');
    sousmenu.innerHTML = '';

    // Utilisation des données passées depuis le json en backend
    let options = menuDocuments[menu] || menuDocuments['Autre'];

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

// Fonction pour gérer l'affichage des onglets
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

// Fonction pour modifier le champs et remplacer le '.' par une ',' dans le champs montant de la facture
function replaceCommaByDot(input) {
    let value = input.value;
    input.value = value.replace(',', '.');
}