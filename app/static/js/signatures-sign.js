/**
 * Signatures - Exécution et signature des documents
 * Utilisé par signature_do.html
 */

// Variables globales pour la signature
let currentSignaturePoint = null;
let signaturePad = null;
let currentScrollPosition = 0;
let acceptanceMandatory = true;

// ===========================================
// INITIALISATION
// ===========================================

document.addEventListener("DOMContentLoaded", function() {
    initializeDocumentSigning();
});

/**
 * Initialise le processus de signature de document
 */
function initializeDocumentSigning() {
    const pdfContainer = document.getElementById('pdf-container');
    const pdfLoader = document.getElementById('pdf-loader');
    
    // Récupérer les données depuis la variable globale documentData (plus fiable que les attributs DOM)
    if (typeof documentData === 'undefined') {
        handleSignatureError(new Error('Données du document manquantes'), 'Initialisation signature');
        return;
    }
    
    const filename = documentData.filename;
    const signaturePoints = documentData.signaturePoints;
    
    if (!filename) {
        handleSignatureError(new Error('Nom de fichier manquant'), 'Initialisation signature');
        return;
    }
    
    if (!signaturePoints) {
        handleSignatureError(new Error('Données de points manquantes'), 'Initialisation signature');
        return;
    }
    
    // Vérifier que signaturePoints est un tableau
    if (!Array.isArray(signaturePoints)) {
        handleSignatureError(new Error('Les données de points ne sont pas un tableau valide'), 'Validation signature');
        return;
    }
    
    try {
        // Initialiser les event listeners
        initializeSigningEventListeners();
        
        // Initialiser le suivi de scroll
        initializeScrollTracking();
        
        // Charger le PDF avec callback pour afficher les points
        initializePDFViewer(filename, pdfLoader, pdfContainer, function() {
            displaySignaturePoints(signaturePoints);
            checkDocumentReadStatus();
        }, false);
        
    } catch (error) {
        handleSignatureError(error, 'Parser points signature');
    }
}

// ===========================================
// EVENT LISTENERS
// ===========================================

/**
 * Initialise les event listeners pour la signature
 */
function initializeSigningEventListeners() {
    // Checkbox d'acceptation des conditions
    const acceptConditions = document.getElementById('accept-conditions');
    if (acceptConditions) {
        acceptConditions.addEventListener('change', updateSignButtonState);
    }
    
    // Checkbox de lecture complète
    const fullRead = document.getElementById('full-read');
    if (fullRead) {
        fullRead.addEventListener('change', updateSignButtonState);
    }
    
    // Boutons de signature dans la modale
    const clearSignature = document.getElementById('clear-signature');
    if (clearSignature) {
        clearSignature.addEventListener('click', clearSignaturePad);
    }
    
    const validateSignature = document.getElementById('validate-signature');
    if (validateSignature) {
        validateSignature.addEventListener('click', validateCurrentSignature);
    }
    
    // Gérer la fermeture de la modale de signature
    const signatureModal = document.getElementById('signatureModal');
    if (signatureModal) {
        signatureModal.addEventListener('hidden.bs.modal', function() {
            if (signaturePad) {
                signaturePad.clear();
            }
            currentSignaturePoint = null;
        });
    }
}

// ===========================================
// AFFICHAGE DES POINTS DE SIGNATURE
// ===========================================

/**
 * Affiche les points de signature sur le PDF
 */
function displaySignaturePoints(points) {
    points.forEach(point => {
        createSigningMarker(point);
    });
}

/**
 * Crée un marqueur de signature cliquable
 */
function createSigningMarker(point) {
    // Trouver la page correspondante
    const pageDiv = document.querySelector(`[data-page-number="${point.pageNum}"]`)?.parentElement;
    if (!pageDiv) {
        console.warn(`Page ${point.pageNum} non trouvée pour le point ${point.id}`);
        return;
    }
    
    const marker = document.createElement('div');
    marker.className = 'signature-marker-signing';
    marker.id = `signing-marker-${point.id}`;
    marker.style.position = 'absolute';
    marker.style.left = `${point.x - 15}px`;
    marker.style.top = `${point.y - 15}px`;
    marker.style.width = '30px';
    marker.style.height = '30px';
    marker.style.backgroundColor = point.signed ? '#198754' : '#0d6efd';
    marker.style.border = '3px solid #fff';
    marker.style.borderRadius = '50%';
    marker.style.cursor = point.signed ? 'default' : 'pointer';
    marker.style.zIndex = '1000';
    marker.style.display = 'flex';
    marker.style.alignItems = 'center';
    marker.style.justifyContent = 'center';
    marker.style.fontSize = '14px';
    marker.style.fontWeight = 'bold';
    marker.style.color = 'white';
    marker.style.boxShadow = '0 3px 6px rgba(0,0,0,0.3)';
    marker.style.transition = 'all 0.2s ease';
    
    // Icône selon l'état
    if (point.signed) {
        marker.innerHTML = '<i class="fas fa-check"></i>';
        marker.title = `Signé par ${point.user_name}`;
    } else {
        marker.innerHTML = '<i class="fas fa-pen"></i>';
        marker.title = `Cliquez pour signer (${point.user_name})`;
        
        // Ajouter l'event listener de clic
        marker.addEventListener('click', function() {
            openSignatureModal(point);
        });
        
        // Effets hover
        marker.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1)';
            this.style.backgroundColor = '#0b5ed7';
        });
        
        marker.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.backgroundColor = '#0d6efd';
        });
    }
    
    pageDiv.appendChild(marker);
}

// ===========================================
// GESTION DE LA MODALE DE SIGNATURE
// ===========================================

/**
 * Ouvre la modale de signature pour un point donné
 */
function openSignatureModal(point) {
    currentSignaturePoint = point;
    
    // Mettre à jour le titre et les informations
    const modalTitle = document.getElementById('signatureModalLabel');
    if (modalTitle) {
        modalTitle.textContent = `Signature requise pour ${point.user_name}`;
    }
    
    const pointInfo = document.getElementById('signature-point-info');
    if (pointInfo) {
        pointInfo.innerHTML = `
            <div class="alert alert-info">
                <strong>Point de signature ${point.id}</strong><br>
                Page ${point.pageNum} - Position (${Math.round(point.x)}, ${Math.round(point.y)})<br>
                Signataire: <strong>${point.user_name}</strong>
            </div>
        `;
    }
    
    // Initialiser le SignaturePad si ce n'est pas déjà fait
    initializeSignaturePad();
    
    // Afficher la modale
    const modal = new bootstrap.Modal(document.getElementById('signatureModal'));
    modal.show();
}

/**
 * Initialise le SignaturePad
 */
function initializeSignaturePad() {
    const canvas = document.getElementById('signature-canvas');
    if (!canvas) {
        console.error('[Signatures Sign] Canvas de signature non trouvé');
        return;
    }
    
    if (!signaturePad) {
        signaturePad = new SignaturePad(canvas, {
            backgroundColor: 'rgba(255, 255, 255, 0)',
            penColor: 'rgb(0, 0, 0)',
            minWidth: 0.5,
            maxWidth: 2.5,
            minDistance: 0.01,
            throttle: 16,
            velocityFilterWeight: 0.7
        });
        
        // Événement de fin de signature
        signaturePad.addEventListener('endStroke', function() {
            updateValidateButtonState();
        });
    }
    
    // Effacer le pad
    signaturePad.clear();
    updateValidateButtonState();
    
    // Redimensionner le canvas
    resizeSignatureCanvas();
}

/**
 * Redimensionne le canvas de signature
 */
function resizeSignatureCanvas() {
    const canvas = document.getElementById('signature-canvas');
    if (!canvas || !signaturePad) return;
    
    const container = canvas.parentElement;
    const containerWidth = container.clientWidth;
    const containerHeight = Math.min(200, containerWidth * 0.4);
    
    // Sauvegarder les données si elles existent
    const data = signaturePad.isEmpty() ? null : signaturePad.toData();
    
    // Redimensionner
    canvas.width = containerWidth;
    canvas.height = containerHeight;
    canvas.style.width = `${containerWidth}px`;
    canvas.style.height = `${containerHeight}px`;
    
    // Restaurer les données
    if (data) {
        signaturePad.fromData(data);
    } else {
        signaturePad.clear();
    }
}

/**
 * Efface le pad de signature
 */
function clearSignaturePad() {
    if (signaturePad) {
        signaturePad.clear();
        updateValidateButtonState();
    }
}

/**
 * Met à jour l'état du bouton de validation
 */
function updateValidateButtonState() {
    const validateBtn = document.getElementById('validate-signature');
    if (validateBtn && signaturePad) {
        validateBtn.disabled = signaturePad.isEmpty();
    }
}

/**
 * Valide la signature actuelle
 */
function validateCurrentSignature() {
    if (!signaturePad || !currentSignaturePoint) {
        handleSignatureError(new Error('Pad de signature ou point non initialisé'), 'Validation signature');
        return;
    }
    
    if (signaturePad.isEmpty()) {
        showNotification('Veuillez tracer votre signature avant de valider.', 'warning');
        return;
    }
    
    try {
        // Générer les données de signature
        const signatureData = {
            pointId: currentSignaturePoint.id,
            svgData: signaturePad.toSVG(),
            jsonData: JSON.stringify(signaturePad.toData()),
            timestamp: new Date().toISOString()
        };
        
        // Envoyer la signature au serveur
        submitSignature(signatureData);
        
    } catch (error) {
        handleSignatureError(error, 'Génération données signature');
    }
}

/**
 * Soumet la signature au serveur
 */
function submitSignature(signatureData) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = window.location.href; // Même URL que la page actuelle
    form.style.display = 'none';
    
    // Ajouter les données de signature
    Object.keys(signatureData).forEach(key => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = signatureData[key];
        form.appendChild(input);
    });
    
    // Ajouter le token CSRF si présent
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (csrfToken) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'csrf_token';
        input.value = csrfToken.getAttribute('content');
        form.appendChild(input);
    }
    
    document.body.appendChild(form);
    form.submit();
}

// ===========================================
// SUIVI DE LECTURE DU DOCUMENT
// ===========================================

/**
 * Initialise le suivi de scroll pour la lecture complète
 */
function initializeScrollTracking() {
    if (!acceptanceMandatory) return;
    
    const pdfContainer = document.getElementById('pdf-container');
    if (!pdfContainer) return;
    
    let scrollTimeout;
    pdfContainer.addEventListener('scroll', function() {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(function() {
            currentScrollPosition = pdfContainer.scrollTop;
            checkDocumentReadStatus();
        }, 100);
    });
}

/**
 * Vérifie si le document a été lu complètement
 */
function checkDocumentReadStatus() {
    if (!acceptanceMandatory) return;
    
    const pdfContainer = document.getElementById('pdf-container');
    const fullReadCheckbox = document.getElementById('full-read');
    
    if (!pdfContainer || !fullReadCheckbox) return;
    
    const scrollTop = pdfContainer.scrollTop;
    const scrollHeight = pdfContainer.scrollHeight;
    const clientHeight = pdfContainer.clientHeight;
    
    // Considérer comme lu si on a scrollé jusqu'à 90% du document
    const readPercentage = (scrollTop + clientHeight) / scrollHeight;
    const isFullyRead = readPercentage >= 0.9;
    
    if (isFullyRead && !fullReadCheckbox.checked) {
        fullReadCheckbox.checked = true;
        fullReadCheckbox.disabled = false;
        
        // Animation pour attirer l'attention
        const checkboxContainer = fullReadCheckbox.closest('.form-check');
        if (checkboxContainer) {
            checkboxContainer.style.animation = 'pulse-green 1.5s ease-in-out';
            setTimeout(() => {
                checkboxContainer.style.animation = '';
            }, 1500);
        }
        
        showNotification('✓ Document lu complètement', 'success');
        updateSignButtonState();
    }
}

/**
 * Met à jour l'état du bouton de signature principal
 */
function updateSignButtonState() {
    const acceptConditions = document.getElementById('accept-conditions');
    const fullRead = document.getElementById('full-read');
    const signButtons = document.querySelectorAll('.btn-sign');
    
    let canSign = true;
    
    if (acceptanceMandatory) {
        if (acceptConditions && !acceptConditions.checked) {
            canSign = false;
        }
        if (fullRead && !fullRead.checked) {
            canSign = false;
        }
    }
    
    signButtons.forEach(btn => {
        btn.disabled = !canSign;
        
        if (canSign) {
            btn.classList.remove('btn-secondary');
            btn.classList.add('btn-primary');
            btn.innerHTML = '<i class="fas fa-pen"></i> Prêt à signer';
        } else {
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-secondary');
            btn.innerHTML = '<i class="fas fa-lock"></i> Complétez les étapes requises';
        }
    });
}

// ===========================================
// GESTION DES REDIMENSIONNEMENTS
// ===========================================

// Redimensionner le canvas lors du redimensionnement de la fenêtre
window.addEventListener('resize', function() {
    if (signaturePad) {
        resizeSignatureCanvas();
    }
});

// Observer les changements de taille de la modale
const resizeObserver = new ResizeObserver(function(entries) {
    if (signaturePad) {
        resizeSignatureCanvas();
    }
});

// Observer la modale de signature
document.addEventListener('DOMContentLoaded', function() {
    const signatureModal = document.getElementById('signatureModal');
    if (signatureModal) {
        resizeObserver.observe(signatureModal);
    }
});

// ===========================================
// STYLES CSS DYNAMIQUES
// ===========================================

// Ajouter les styles pour l'animation pulse-green
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(25, 135, 84, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(25, 135, 84, 0); }
        100% { box-shadow: 0 0 0 0 rgba(25, 135, 84, 0); }
    }
    
    .signature-marker-signing:hover {
        transform: scale(1.1) !important;
    }
    
    #signature-canvas {
        border: 2px solid #dee2e6;
        border-radius: 0.375rem;
        cursor: crosshair;
    }
`;
document.head.appendChild(style);
