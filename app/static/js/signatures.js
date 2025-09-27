document.addEventListener("DOMContentLoaded", function() {
    const loader = document.getElementById('pdf-loader');
    const pdfContainer = document.getElementById('pdf-container');
    loader.style.display = "flex";
    pdfContainer.style.display = "none";

    // construction de l'URL du PDF à partir du nom de fichier
    const filename = pdfContainer.getAttribute('data-filename');
    const url = `/signature/download/${filename}?temp_dir=True`;

    // Handler for rendering a page
    function handlePageRender(pageNum, numPages, loader, pdfContainer, page, scale) {
        const viewport = page.getViewport({ scale: scale });

        // Créer un conteneur pour cette page
        const pageDiv = document.createElement('div');
        pageDiv.className = 'pdf-page';
        pageDiv.style.marginBottom = '10px';
        
        // Préparation du canvas
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        
        pageDiv.appendChild(canvas);
        pdfContainer.appendChild(pageDiv);

        // Rendu de la page
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        
        page.render(renderContext).promise.then(function() {
            // Si c'est la dernière page, masquer le loader et activer les clics
            if (pageNum === numPages) {
                loader.style.display = "none";
                pdfContainer.style.display = "block";
                // Activer l'écoute des clics sur le PDF
                addClickListenerToPDF();
            }
        });
    }

    // Fonction pour rendre une page
    function renderPage(pdf, pageNum, numPages, loader, pdfContainer, scale) {
        pdf.getPage(pageNum).then(function(page) {
            handlePageRender(pageNum, numPages, loader, pdfContainer, page, scale);
        });
    }

    // Chargement du PDF avec PDF.js
    const loadingTask = pdfjsLib.getDocument(url);
    loadingTask.promise.then(function(pdf) {
        const scale = 1.5;
        const numPages = pdf.numPages;
        
        // Vider le conteneur
        pdfContainer.innerHTML = '';
        
        // Rendre toutes les pages
        for (let pageNum = 1; pageNum <= numPages; pageNum++) {
            renderPage(pdf, pageNum, numPages, loader, pdfContainer, scale);
        }
        
    }, function(reason) {
        // Erreur lors du chargement du PDF
        console.error(reason);
    });
});

// Variables globales pour la gestion des points de signature
let signaturePoints = [];
let signaturePointCounter = 0;

// Fonction pour créer un point de signature
function createSignaturePoint(x, y, pageNum, pageDiv) {
    signaturePointCounter++;
    const pointId = `signature-point-${signaturePointCounter}`;
    
    // Créer le marqueur visuel sur le PDF
    const marker = document.createElement('div');
    marker.className = 'signature-marker';
    marker.id = pointId;
    marker.style.position = 'absolute';
    marker.style.left = `${x - 10}px`;
    marker.style.top = `${y - 10}px`;
    marker.style.width = '24px';
    marker.style.height = '24px';
    marker.style.backgroundColor = '#ff4444';
    marker.style.border = '2px solid #cc0000';
    marker.style.borderRadius = '50%';
    marker.style.cursor = 'pointer';
    marker.style.zIndex = '1000';
    marker.style.display = 'flex';
    marker.style.alignItems = 'center';
    marker.style.justifyContent = 'center';
    marker.style.fontSize = '12px';
    marker.style.fontWeight = 'bold';
    marker.style.color = 'white';
    marker.style.textShadow = '1px 1px 1px rgba(0,0,0,0.5)';
    marker.textContent = signaturePointCounter;
    marker.title = `Point de signature ${signaturePointCounter}`;
    
    // Positionner le conteneur de page en relatif
    pageDiv.style.position = 'relative';
    pageDiv.appendChild(marker);
    
    // Créer l'objet point de signature
    const signaturePoint = {
        id: pointId,
        counter: signaturePointCounter,
        x: x,
        y: y,
        pageNum: pageNum,
        userId: null,
        validated: false,
        marker: marker
    };
    
    signaturePoints.push(signaturePoint);
    
    // Ajouter dans le panel de droite
    addSignaturePointToPanel(signaturePoint);
    
    return signaturePoint;
}

// Fonction pour ajouter un point de signature dans le panel
function addSignaturePointToPanel(signaturePoint) {
    const pointsList = document.getElementById('signature-points-list');
    
    const pointItem = document.createElement('div');
    pointItem.className = 'signature-point-item';
    pointItem.id = `panel-${signaturePoint.id}`;
    
    pointItem.innerHTML = `
        <h6>Point ${signaturePoint.counter} (Page ${signaturePoint.pageNum})</h6>
        <div class="mb-2">
            <select class="form-select form-select-sm" id="user-select-${signaturePoint.id}">
                <option value="">Sélectionner un signataire</option>
                <!-- Les options seront ajoutées dynamiquement -->
            </select>
        </div>
        <div class="btn-group w-100" role="group">
            <button type="button" class="btn btn-sm btn-success" onclick="validateSignaturePoint('${signaturePoint.id}')">
                Valider
            </button>
            <button type="button" class="btn btn-sm btn-danger" onclick="removeSignaturePoint('${signaturePoint.id}')">
                Supprimer
            </button>
        </div>
    `;
    
    pointsList.appendChild(pointItem);
    
    // Ajouter les options utilisateurs (à implémenter selon tes données)
    populateUserSelect(`user-select-${signaturePoint.id}`);
}

// Fonction pour peupler la liste des utilisateurs
function populateUserSelect(selectId) {
    const select = document.getElementById(selectId);
    
    // Utiliser la variable users depuis le template Jinja
    if (typeof users !== 'undefined' && users.length > 0) {
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = user.nom + ' ' + user.prenom;
            select.appendChild(option);
        });
    } else {
        // Fallback si pas d'utilisateurs
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'Aucun utilisateur disponible';
        select.appendChild(option);
    }
}

// Fonction pour valider un point de signature
function validateSignaturePoint(pointId) {
    const point = signaturePoints.find(p => p.id === pointId);
    const userSelect = document.getElementById(`user-select-${pointId}`);
    
    if (!userSelect.value) {
        alert('Veuillez sélectionner un signataire');
        return;
    }
    
    point.userId = userSelect.value;
    point.validated = true;
    
    // Changer l'apparence du marqueur
    point.marker.style.backgroundColor = '#44ff44';
    point.marker.style.border = '2px solid #00cc00';
    
    // Modifier les boutons dans le panel
    const panelItem = document.getElementById(`panel-${pointId}`);
    const buttonGroup = panelItem.querySelector('.btn-group');
    buttonGroup.innerHTML = `
        <button type="button" class="btn btn-sm btn-warning" onclick="editSignaturePoint('${pointId}')">
            Modifier
        </button>
        <button type="button" class="btn btn-sm btn-danger" onclick="removeSignaturePoint('${pointId}')">
            Supprimer
        </button>
    `;
    
    // Désactiver le select
    userSelect.disabled = true;
    
    // Ajouter un champ caché au formulaire
    addHiddenInputToForm(point);
}

// Fonction pour éditer un point de signature
function editSignaturePoint(pointId) {
    const point = signaturePoints.find(p => p.id === pointId);
    const userSelect = document.getElementById(`user-select-${pointId}`);
    
    point.validated = false;
    
    // Remettre l'apparence originale du marqueur
    point.marker.style.backgroundColor = '#ff4444';
    point.marker.style.border = '2px solid #cc0000';
    
    // Remettre les boutons originaux
    const panelItem = document.getElementById(`panel-${pointId}`);
    const buttonGroup = panelItem.querySelector('.btn-group');
    buttonGroup.innerHTML = `
        <button type="button" class="btn btn-sm btn-success" onclick="validateSignaturePoint('${pointId}')">
            Valider
        </button>
        <button type="button" class="btn btn-sm btn-danger" onclick="removeSignaturePoint('${pointId}')">
            Supprimer
        </button>
    `;
    
    // Réactiver le select
    userSelect.disabled = false;
    
    // Supprimer le champ caché du formulaire
    removeHiddenInputFromForm(pointId);
}

// Fonction pour supprimer un point de signature
function removeSignaturePoint(pointId) {
    const pointIndex = signaturePoints.findIndex(p => p.id === pointId);
    
    if (pointIndex !== -1) {
        // Supprimer le marqueur du PDF
        const point = signaturePoints[pointIndex];
        point.marker.remove();
        
        // Supprimer du panel
        const panelItem = document.getElementById(`panel-${pointId}`);
        panelItem.remove();
        
        // Supprimer du tableau
        signaturePoints.splice(pointIndex, 1);
        
        // Supprimer le champ caché du formulaire
        removeHiddenInputFromForm(pointId);
    }
}

// Fonction pour ajouter un champ caché au formulaire
function addHiddenInputToForm(point) {
    const form = document.getElementById('signer-form');
    
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = `signature_points[${point.counter}]`;
    input.id = `hidden-${point.id}`;
    input.value = JSON.stringify({
        x: point.x,
        y: point.y,
        pageNum: point.pageNum,
        userId: point.userId
    });
    
    form.appendChild(input);
}

// Fonction pour supprimer un champ caché du formulaire
function removeHiddenInputFromForm(pointId) {
    const hiddenInput = document.getElementById(`hidden-${pointId}`);
    if (hiddenInput) {
        hiddenInput.remove();
    }
}

// Fonctionnalité de marquage des points de signature - écouteur de clic
function addClickListenerToPDF() {
    const pdfContainer = document.getElementById('pdf-container');
    
    pdfContainer.addEventListener('click', function(event) {
        // Vérifier si le clic est sur un canvas (page PDF)
        if (event.target.tagName === 'CANVAS') {
            const canvas = event.target;
            const pageDiv = canvas.parentElement;
            const rect = canvas.getBoundingClientRect();
            
            // Calculer les coordonnées relatives au canvas
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            // Trouver le numéro de page
            const allPages = pdfContainer.querySelectorAll('.pdf-page');
            const pageNum = Array.from(allPages).indexOf(pageDiv) + 1;
            
            // Créer le point de signature
            createSignaturePoint(x, y, pageNum, pageDiv);
        }
    });
}


