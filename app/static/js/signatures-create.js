/**
 * Signatures - Création et configuration des documents
 * Utilisé par signature_make.html
 */

// Variables globales pour la création
let signaturePoints = [];
let signaturePointCounter = 0;

// ===========================================
// INITIALISATION
// ===========================================

document.addEventListener("DOMContentLoaded", function() {
    initializeDocumentCreation();
});

/**
 * Initialise le processus de création de document
 */
function initializeDocumentCreation() {
    const pdfContainer = document.getElementById('pdf-container');
    const pdfLoader = document.getElementById('pdf-loader');
    
    if (!pdfContainer || !pdfLoader) {
        console.log('[Signatures Create] Éléments non trouvés - pas le bon template');
        return;
    }
    
    console.log('[Signatures Create] Initialisation de la création de document');
    
    // Récupérer le nom du fichier
    const filename = pdfContainer.getAttribute('data-filename');
    if (!filename) {
        handleSignatureError(new Error('Nom de fichier manquant'), 'Initialisation création');
        return;
    }
    
    // Initialiser les event listeners
    initializeCreationEventListeners();
    
    // Charger le PDF avec callback pour activer les clics
    initializePDFViewer(filename, pdfLoader, pdfContainer, function() {
        addClickListenerToPDF();
        updateConfigureButton();
    });
}

// ===========================================
// EVENT LISTENERS
// ===========================================

/**
 * Initialise les event listeners pour la création
 */
function initializeCreationEventListeners() {
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

// ===========================================
// GESTION DES POINTS DE SIGNATURE
// ===========================================

/**
 * Ajoute l'écouteur de clic sur le PDF
 */
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
            const pageNum = parseInt(canvas.getAttribute('data-page-number')) || 1;
            
            // Créer le point de signature
            createSignaturePoint(x, y, pageNum, pageDiv);
        }
    });
}

/**
 * Crée un nouveau point de signature
 */
function createSignaturePoint(x, y, pageNum, pageDiv) {
    signaturePointCounter++;
    const pointId = signaturePointCounter;
    
    // Créer le marqueur visuel sur le PDF
    const marker = createVisualMarker(pointId, x, y, pageNum, pageDiv);
    
    // Créer l'objet point de signature
    const signaturePoint = {
        id: pointId,
        x: parseFloat(x.toFixed(2)),
        y: parseFloat(y.toFixed(2)),
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

/**
 * Crée un marqueur visuel sur le PDF
 */
function createVisualMarker(pointId, x, y, pageNum, pageDiv) {
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
    
    pageDiv.appendChild(marker);
    return marker;
}

/**
 * Ajoute un point de signature dans le panel
 */
function addSignaturePointToPanel(signaturePoint) {
    const pointsList = document.getElementById('signature-points-list');
    if (!pointsList) return;
    
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

/**
 * Peuple la liste des utilisateurs dans un select
 */
function populateUserSelect(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;
    
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

// ===========================================
// GESTION DES ÉTATS DES POINTS
// ===========================================

/**
 * Appelée quand un utilisateur est sélectionné
 */
function onUserSelected(pointId) {
    const select = document.getElementById(`user-select-${pointId}`);
    const validateBtn = document.getElementById(`validate-${pointId}`);
    
    if (select && validateBtn) {
        validateBtn.disabled = !select.value;
    }
}

/**
 * Valide un point de signature
 */
function validateSignaturePoint(pointId) {
    const point = signaturePoints.find(p => p.id === pointId);
    if (!point) return;

    const userSelect = document.getElementById(`user-select-${pointId}`);
    const selectedUserId = userSelect.value;
    
    if (!selectedUserId) {
        showNotification('Veuillez sélectionner un utilisateur.', 'warning');
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
    
    showNotification(`Point ${pointId} assigné à ${point.user_name}`, 'success');
}

/**
 * Édite un point de signature
 */
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

/**
 * Supprime un point de signature
 */
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
    
    showNotification(`Point ${pointId} supprimé`, 'info');
}

/**
 * Met à jour l'apparence du marqueur visuel
 */
function updateVisualMarker(pointId, validated) {
    const marker = document.getElementById(`marker-${pointId}`);
    if (!marker) return;
    
    if (validated) {
        marker.style.backgroundColor = '#198754';
    } else {
        marker.style.backgroundColor = '#dc3545';
    }
}

// ===========================================
// GESTION DU BOUTON DE CONFIGURATION
// ===========================================

/**
 * Met à jour l'état du bouton de configuration
 */
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

// ===========================================
// GESTION DE LA MODALE DE CONFIGURATION
// ===========================================

/**
 * Affiche la modale de configuration
 */
function showDocumentConfigModal() {
    updateSignersSummary();
    const modal = new bootstrap.Modal(document.getElementById('documentConfigModal'));
    modal.show();
}

/**
 * Met à jour le récapitulatif des signataires
 */
function updateSignersSummary() {
    const summaryDiv = document.getElementById('signers-summary');
    if (!summaryDiv) return;
    
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

/**
 * Soumet le document complet
 */
function submitCompleteDocument() {
    const configForm = document.getElementById('document-config-form');
    const signatureForm = document.getElementById('signature-form');
    
    if (!configForm || !signatureForm) {
        handleSignatureError(new Error('Formulaires non trouvés'), 'Soumission document');
        return;
    }
    
    // Valider le formulaire de configuration
    if (!configForm.checkValidity()) {
        configForm.reportValidity();
        return;
    }
    
    try {
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
        
        // Afficher un message de chargement
        showNotification('Envoi du document en cours...', 'info');
        
        // Soumettre le formulaire
        signatureForm.submit();
        
    } catch (error) {
        handleSignatureError(error, 'Soumission document');
    }
}

console.log('[Signatures Create] Module chargé avec succès');