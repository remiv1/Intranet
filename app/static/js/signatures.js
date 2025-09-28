// Variables globales pour la gestion des points de signature
let signaturePoints = [];
let signaturePointCounter = 0;

document.addEventListener("DOMContentLoaded", function() {
    const loader = document.getElementById('pdf-loader');
    const pdfContainer = document.getElementById('pdf-container');
    loader.style.display = "flex";
    pdfContainer.style.display = "none";

    // construction de l'URL du PDF à partir du nom de fichier
    const filename = pdfContainer.getAttribute('data-filename');
    const url = `/signature/download/${filename}?temp_dir=True`;
    
    // Initialiser les event listeners
    initializeEventListeners();

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
                // Initialiser l'état du bouton de configuration
                updateConfigureButton();
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

// Fonction pour mettre à jour l'état du bouton de configuration
function updateConfigureButton() {
    const configureBtn = document.getElementById('configure-document');
    if (!configureBtn) return;
    
    const hasPoints = signaturePoints.length > 0;
    const allValidated = signaturePoints.every(point => point.validated);
    
    if (hasPoints && allValidated) {
        configureBtn.disabled = false;
        configureBtn.innerHTML = `<i class="fas fa-cog"></i> Configurer le document (${signaturePoints.length} signature${signaturePoints.length > 1 ? 's' : ''})`;
        configureBtn.className = 'btn btn-success mt-3';
    } else if (hasPoints && !allValidated) {
        configureBtn.disabled = true;
        const validatedCount = signaturePoints.filter(p => p.validated).length;
        configureBtn.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${validatedCount}/${signaturePoints.length} points validés`;
        configureBtn.className = 'btn btn-warning mt-3';
    } else {
        configureBtn.disabled = true;
        configureBtn.innerHTML = '<i class="fas fa-info-circle"></i> Ajoutez des points de signature';
        configureBtn.className = 'btn btn-secondary mt-3';
    }
}

// Fonction pour créer un point de signature
function createSignaturePoint(x, y, pageNum, pageDiv) {
    signaturePointCounter++;
    const pointId = signaturePointCounter;
    
    // Créer le marqueur visuel sur le PDF
    const marker = document.createElement('div');
    marker.className = 'signature-marker';
    marker.id = `marker-${pointId}`;
    marker.style.position = 'absolute';
    marker.style.left = `${x - 12}px`;
    marker.style.top = `${y - 12}px`;
    marker.style.width = '24px';
    marker.style.height = '24px';
    marker.style.backgroundColor = '#dc3545';
    marker.style.border = '2px solid #fff';
    marker.style.borderRadius = '50%';
    marker.style.cursor = 'pointer';
    marker.style.zIndex = '1000';
    marker.style.display = 'flex';
    marker.style.alignItems = 'center';
    marker.style.justifyContent = 'center';
    marker.style.fontSize = '12px';
    marker.style.fontWeight = 'bold';
    marker.style.color = 'white';
    marker.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
    marker.textContent = pointId;
    marker.title = `Point de signature ${pointId}`;
    
    // Positionner le conteneur de page en relatif
    pageDiv.style.position = 'relative';
    pageDiv.appendChild(marker);
    
    // Créer l'objet point de signature
    const signaturePoint = {
        id: pointId,
        x: x,
        y: y,
        pageNum: pageNum,
        user_id: null,
        user_name: null,
        validated: false,
        marker: marker
    };
    
    signaturePoints.push(signaturePoint);
    
    // Ajouter dans le panel de droite
    addSignaturePointToPanel(signaturePoint);
    
    // Mettre à jour le bouton de configuration
    updateConfigureButton();
    
    return signaturePoint;
}

// Fonction pour ajouter un point de signature dans le panel
function addSignaturePointToPanel(signaturePoint) {
    const pointsList = document.getElementById('signature-points-list');
    
    const pointElement = document.createElement('div');
    pointElement.id = `signature-point-${signaturePoint.id}`;
    pointElement.className = 'signature-point mb-3 p-3 border rounded bg-light';
    
    pointElement.innerHTML = `
        <div class="d-flex justify-content-between align-items-start mb-2">
            <strong>Point ${signaturePoint.id}</strong>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeSignaturePoint(${signaturePoint.id})">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <small class="text-muted">Page ${signaturePoint.pageNum} - Position (${Math.round(signaturePoint.x)}, ${Math.round(signaturePoint.y)})</small>
        <div class="mt-2">
            <select id="user-select-${signaturePoint.id}" class="form-select form-select-sm mb-2" onchange="onUserSelected(${signaturePoint.id})">
                <option value="">Sélectionner un signataire...</option>
            </select>
            <button type="button" id="validate-${signaturePoint.id}" class="btn btn-sm btn-success" onclick="validateSignaturePoint(${signaturePoint.id})" disabled>
                Valider
            </button>
        </div>
    `;
    
    pointsList.appendChild(pointElement);
    
    // Ajouter les options utilisateurs
    populateUserSelect(`user-select-${signaturePoint.id}`);
}

// Fonction appelée quand un utilisateur est sélectionné
function onUserSelected(pointId) {
    const select = document.getElementById(`user-select-${pointId}`);
    const validateBtn = document.getElementById(`validate-${pointId}`);
    
    if (select.value) {
        validateBtn.disabled = false;
    } else {
        validateBtn.disabled = true;
    }
}

// Fonction pour peupler la liste des utilisateurs
function populateUserSelect(selectId) {
    const select = document.getElementById(selectId);
    
    // Utiliser la variable users depuis le template Jinja
    if (typeof users !== 'undefined' && users.length > 0) {
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = `${user.nom} ${user.prenom}`;
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
    if (!point) return;

    const userSelect = document.getElementById(`user-select-${pointId}`);
    const selectedUserId = userSelect.value;
    
    if (!selectedUserId) {
        alert('Veuillez sélectionner un utilisateur.');
        return;
    }

    const selectedUser = users.find(u => u.id == selectedUserId);
    if (!selectedUser) return;

    // Marquer comme validé
    point.validated = true;
    point.user_id = selectedUserId;
    point.user_name = `${selectedUser.nom} ${selectedUser.prenom}`;

    // Mettre à jour l'affichage
    const pointElement = document.getElementById(`signature-point-${pointId}`);
    pointElement.classList.add('border-success', 'bg-success-subtle');

    const validateBtn = document.getElementById(`validate-${pointId}`);
    validateBtn.textContent = 'Modifier';
    validateBtn.className = 'btn btn-sm btn-warning';
    validateBtn.onclick = () => editSignaturePoint(pointId);

    // Désactiver le select
    userSelect.disabled = true;
    
    // Mettre à jour le marqueur visuel
    updateVisualMarker(pointId, true);

    // Mettre à jour le bouton de configuration
    updateConfigureButton();
}

// Fonction pour éditer un point de signature
function editSignaturePoint(pointId) {
    const point = signaturePoints.find(p => p.id === pointId);
    if (!point) return;

    // Marquer comme non validé
    point.validated = false;
    point.user_id = null;
    point.user_name = null;

    // Mettre à jour l'affichage
    const pointElement = document.getElementById(`signature-point-${pointId}`);
    pointElement.classList.remove('border-success', 'bg-success-subtle');

    const validateBtn = document.getElementById(`validate-${pointId}`);
    validateBtn.textContent = 'Valider';
    validateBtn.className = 'btn btn-sm btn-success';
    validateBtn.onclick = () => validateSignaturePoint(pointId);

    // Réactiver le select
    const userSelect = document.getElementById(`user-select-${pointId}`);
    userSelect.disabled = false;
    
    // Mettre à jour le marqueur visuel
    updateVisualMarker(pointId, false);

    // Mettre à jour le bouton de configuration
    updateConfigureButton();
}

// Fonction pour supprimer un point de signature
function removeSignaturePoint(pointId) {
    // Supprimer du DOM
    const pointElement = document.getElementById(`signature-point-${pointId}`);
    if (pointElement) pointElement.remove();

    // Supprimer le marqueur visuel
    const marker = document.getElementById(`marker-${pointId}`);
    if (marker) marker.remove();

    // Supprimer du tableau
    const index = signaturePoints.findIndex(p => p.id === pointId);
    if (index > -1) {
        signaturePoints.splice(index, 1);
    }

    // Mettre à jour le bouton de configuration
    updateConfigureButton();
}

// Fonction pour mettre à jour l'apparence du marqueur visuel
function updateVisualMarker(pointId, validated) {
    const marker = document.getElementById(`marker-${pointId}`);
    if (!marker) return;
    
    if (validated) {
        marker.style.backgroundColor = '#198754';
    } else {
        marker.style.backgroundColor = '#dc3545';
    }
}

// Fonction pour afficher la modale de configuration
function showDocumentConfigModal() {
    updateSignersSummary();
    const modal = new bootstrap.Modal(document.getElementById('documentConfigModal'));
    modal.show();
}

// Fonction pour mettre à jour le récapitulatif des signataires
function updateSignersSummary() {
    const summaryDiv = document.getElementById('signers-summary');
    const validatedPoints = signaturePoints.filter(point => point.validated);
    
    if (validatedPoints.length === 0) {
        summaryDiv.innerHTML = '<p class="text-muted">Aucun signataire configuré</p>';
        return;
    }
    
    let html = '<ul class="list-unstyled mb-0">';
    validatedPoints.forEach((point, index) => {
        html += `
            <li class="d-flex justify-content-between align-items-center py-2 ${index > 0 ? 'border-top' : ''}">
                <div>
                    <strong>Point ${point.id}</strong> - ${point.user_name}
                    <br><small class="text-muted">Page ${point.pageNum}, Position (${Math.round(point.x)}, ${Math.round(point.y)})</small>
                </div>
                <span class="badge bg-success">Configuré</span>
            </li>
        `;
    });
    html += '</ul>';
    
    summaryDiv.innerHTML = html;
}

// Fonction pour soumettre le document complet
function submitCompleteDocument() {
    const configForm = document.getElementById('document-config-form');
    const signatureForm = document.getElementById('signature-form');
    
    // Valider le formulaire de configuration
    if (!configForm.checkValidity()) {
        configForm.reportValidity();
        return;
    }
    
    // Ajouter les données de configuration au formulaire principal
    const formData = new FormData(configForm);
    formData.forEach((value, key) => {
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = key;
        hiddenInput.value = value;
        signatureForm.appendChild(hiddenInput);
    });
    
    // Ajouter les points de signature validés
    const validatedPoints = signaturePoints.filter(point => point.validated);
    validatedPoints.forEach((point, index) => {
        ['x', 'y', 'pageNum', 'user_id'].forEach(field => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = `signature_points[${index}][${field}]`;
            input.value = point[field];
            signatureForm.appendChild(input);
        });
    });
    
    // Fermer la modale
    const modal = bootstrap.Modal.getInstance(document.getElementById('documentConfigModal'));
    if (modal) {
        modal.hide();
    }
    
    // Soumettre le formulaire
    signatureForm.submit();
}

// Fonction pour initialiser les event listeners
function initializeEventListeners() {
    // Bouton de configuration
    const configureBtn = document.getElementById('configure-document');
    if (configureBtn) {
        configureBtn.addEventListener('click', function() {
            if (!this.disabled) {
                showDocumentConfigModal();
            }
        });
    }
    
    // Bouton de soumission dans la modale
    const submitBtn = document.getElementById('submit-document');
    if (submitBtn) {
        submitBtn.addEventListener('click', submitCompleteDocument);
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


