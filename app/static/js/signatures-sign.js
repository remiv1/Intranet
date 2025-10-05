/**
 * Signatures - Signature graphique avec validation OTP
 * Utilisé par signature_do.html
 */

// Variables globales
let hasReadDocument = false;
let signaturePad = null;
let token = null;
let hashDocument = null;
let documentId = null;

// Variables pour capture haute précision
let customSignatureData = {
    strokes: [],
    currentStroke: null,
    precision: 0.01 // Précision en pixels
};

// ===========================================
// Listener sur le DOMContentLoaded
// ===========================================

document.addEventListener("DOMContentLoaded", function() {
    initializeDocumentSigning();
    token = document.getElementById('invit-token') ? document.getElementById('invit-token').value : null;
    hashDocument = document.getElementById('hash-document') ? document.getElementById('hash-document').value : null;
    documentId = document.getElementById('doc-id') ? document.getElementById('doc-id').value : null;
});

// ===========================================
// INITIALISATION
// ===========================================

function initializeDocumentSigning() {
    const pdfContainer = document.getElementById('pdf-container');
    const pdfLoader = document.getElementById('pdf-loader');
    const filename = documentData.filename;
    const signaturePoints = documentData.signaturePoints;
    
    console.log('Initialisation avec les points:', signaturePoints);
    
    // Initialiser les event listeners
    initializeEventListeners();
    
    // Initialiser le suivi de scroll
    initializeScrollTracking();
    
    // Charger le PDF avec callback pour afficher les points
    initializePDFViewer(filename, pdfLoader, pdfContainer, function() {
        console.log('PDF chargé, affichage des points');
        displaySignaturePoints(signaturePoints);
    }, false);
}

// ===========================================
// EVENT LISTENERS
// ===========================================

function initializeEventListeners() {
    // Cases à cocher d'acceptation
    const acceptContent = document.getElementById('accept-content');
    const acceptElectronic = document.getElementById('accept-electronic-signature');
    const acceptLegal = document.getElementById('accept-legal-value');
    
    if (acceptContent) {
        acceptContent.addEventListener('change', updateSignButtonState);
    }
    if (acceptElectronic) {
        acceptElectronic.addEventListener('change', updateSignButtonState);
    }
    if (acceptLegal) {
        acceptLegal.addEventListener('change', updateSignButtonState);
    }
    
    // Bouton "Procéder à la signature"
    const signButton = document.getElementById('btn-sign');
    if (signButton) {
        signButton.addEventListener('click', function() {
            console.log('Clic sur le bouton de signature, déclenchement OTP');
            requestOTPCode();
        });
    }
    
    // Vérifier l'état initial du bouton
    updateSignButtonState();
}

// ===========================================
// AFFICHAGE DES POINTS DE SIGNATURE
// ===========================================

function displaySignaturePoints(points) {
    console.log('=== AFFICHAGE DES POINTS DE SIGNATURE ===');
    console.log('Nombre de points à afficher:', points ? points.length : 0);
    console.log('Points reçus:', points);
    
    if (!points || !Array.isArray(points)) {
        console.error('Points de signature invalides:', points);
        return;
    }
    
    // Vérifier que toutes les pages sont bien présentes dans le DOM
    const pdfPages = document.querySelectorAll('.pdf-page');
    console.log('Nombre de pages PDF dans le DOM:', pdfPages.length);
    pdfPages.forEach((page, index) => {
        const pageNum = page.getAttribute('data-page-number');
        console.log(`Page ${index + 1} dans le DOM a data-page-number="${pageNum}"`);
    });
    
    points.forEach((point, index) => {
        console.log(`\n--- Traitement du point ${index + 1}/${points.length} ---`);
        console.log('Données du point:', point);
        createSignatureRectangle(point);
    });
    
    console.log('=== FIN AFFICHAGE DES POINTS ===\n');
}

function createSignatureRectangle(viewPoint) {
    // Extraire les données du point depuis la structure ViewPoints
    const point = viewPoint.point || viewPoint;
    const user = viewPoint.user || {};
    const userName = viewPoint.user_complete_name || user.nom || 'Signataire';
    
    console.log('Point extrait:', point);
    console.log('page_num du point:', point.page_num);
    console.log('Type de page_num:', typeof point.page_num);
    
    // Trouver le conteneur de page (div.pdf-page) directement
    let pageDiv = document.querySelector(`.pdf-page[data-page-number="${point.page_num}"]`);
    console.log(`Recherche avec .pdf-page[data-page-number="${point.page_num}"]`, pageDiv ? 'TROUVÉ' : 'NON TROUVÉ');
    
    if (!pageDiv && point.pageNum) {
        pageDiv = document.querySelector(`.pdf-page[data-page-number="${point.pageNum}"]`);
        console.log(`Recherche avec .pdf-page[data-page-number="${point.pageNum}"]`, pageDiv ? 'TROUVÉ' : 'NON TROUVÉ');
    }
    if (!pageDiv && point.page) {
        pageDiv = document.querySelector(`.pdf-page[data-page-number="${point.page}"]`);
        console.log(`Recherche avec .pdf-page[data-page-number="${point.page}"]`, pageDiv ? 'TROUVÉ' : 'NON TROUVÉ');
    }
    
    if (!pageDiv) {
        console.error(`❌ ERREUR: Page ${point.page_num} non trouvée pour le point ${point.id}`);
        console.error('Propriétés du point disponibles:', Object.keys(point));
        console.error('Valeurs du point:', point);
        
        // Lister toutes les pages disponibles
        const allPages = document.querySelectorAll('.pdf-page[data-page-number]');
        console.error('Pages disponibles dans le DOM:');
        allPages.forEach(p => {
            console.error(`  - Page ${p.getAttribute('data-page-number')} (${p.tagName})`);
        });
        return;
    }
    
    console.log(`✅ Page ${point.page_num} trouvée:`, pageDiv);
    
    // S'assurer que la page a position: relative pour les enfants absolus
    if (getComputedStyle(pageDiv).position === 'static') {
        pageDiv.style.position = 'relative';
    }
    
    const rectangle = document.createElement('div');
    rectangle.className = 'signature-rectangle';
    rectangle.id = `signature-rect-${point.id}`;
    rectangle.style.position = 'absolute';
    rectangle.style.left = `${point.x - 50}px`; // Centré sur le point
    rectangle.style.top = `${point.y - 15}px`;  // Centré sur le point
    rectangle.style.width = '100px';
    rectangle.style.height = '30px';
    rectangle.style.backgroundColor = 'rgba(25, 135, 84, 0.25)'; // Vert avec 75% de transparence
    rectangle.style.border = '2px solid #198754';
    rectangle.style.borderRadius = '4px';
    rectangle.style.zIndex = '1000';
    rectangle.style.display = 'flex';
    rectangle.style.alignItems = 'center';
    rectangle.style.justifyContent = 'center';
    rectangle.style.fontSize = '12px';
    rectangle.style.fontWeight = 'bold';
    rectangle.style.color = '#198754';
    rectangle.style.pointerEvents = 'none';
    
    // Texte dans le rectangle
    rectangle.innerHTML = 'Signature';
    rectangle.title = `Zone de signature pour ${userName} - Page ${point.page_num}`;
    
    pageDiv.appendChild(rectangle);
    console.log(`Rectangle de signature créé et ajouté à la page ${point.page_num}:`, rectangle);
}

// ===========================================
// SUIVI DE LECTURE DU DOCUMENT
// ===========================================

function initializeScrollTracking() {
    const pdfContainer = document.getElementById('pdf-container');
    if (!pdfContainer) return;
    
    let scrollTimeout;
    pdfContainer.addEventListener('scroll', function() {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(function() {
            checkDocumentReadStatus();
        }, 100);
    });
}

function checkDocumentReadStatus() {
    const pdfContainer = document.getElementById('pdf-container');
    const acceptanceSection = document.getElementById('acceptance-section');
    
    if (!pdfContainer || !acceptanceSection || hasReadDocument) return;
    
    const scrollTop = pdfContainer.scrollTop;
    const scrollHeight = pdfContainer.scrollHeight;
    const clientHeight = pdfContainer.clientHeight;
    
    // Considérer comme lu si on a scrollé jusqu'à 90% du document
    const readPercentage = (scrollTop + clientHeight) / scrollHeight;
    const isFullyRead = readPercentage >= 0.9;
    
    if (isFullyRead) {
        hasReadDocument = true;
        
        // Afficher la section d'acceptation
        acceptanceSection.classList.remove('d-none');
        
        // Animation pour attirer l'attention
        acceptanceSection.style.animation = 'fadeIn 0.5s ease-in-out';
        
        console.log('Document lu complètement, affichage des cases de validation');
    }
}

function updateSignButtonState() {
    console.log('Vérification de l\'état des cases à cocher...');
    
    const acceptContent = document.getElementById('accept-content');
    const acceptElectronic = document.getElementById('accept-electronic-signature');
    const acceptLegal = document.getElementById('accept-legal-value');
    const signButton = document.getElementById('btn-sign');
    
    if (!acceptContent || !acceptElectronic || !acceptLegal || !signButton) {
        console.log('Éléments non trouvés');
        return;
    }
    
    console.log('État des cases:', {
        acceptContent: acceptContent.checked,
        acceptElectronic: acceptElectronic.checked,
        acceptLegal: acceptLegal.checked
    });
    
    // Vérifier si toutes les cases sont cochées
    const allChecked = acceptContent.checked && acceptElectronic.checked && acceptLegal.checked;
    
    // Activer/désactiver le bouton selon l'état des cases
    signButton.disabled = !allChecked;
    
    if (allChecked) {
        signButton.classList.remove('btn-secondary');
        signButton.classList.add('btn-primary');
        signButton.innerHTML = '<i class="fas fa-pen"></i> Procéder à la signature';
        console.log('Bouton de signature activé');
    } else {
        signButton.classList.remove('btn-primary');
        signButton.classList.add('btn-secondary');
        signButton.innerHTML = '<i class="fas fa-lock"></i> Complétez les étapes requises';
        console.log('Bouton de signature désactivé');
    }
}

// ===========================================
// GESTION OTP ET SIGNATURE
// ===========================================

function requestOTPCode() {
    console.log('Demande de code OTP...');
    
    // Désactiver le bouton pendant la requête
    const signButton = document.getElementById('btn-sign');
    if (signButton) {
        signButton.disabled = true;
        signButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Envoi du code...';
    }
    
    // Envoyer une requête pour créer la signature et envoyer l'OTP
    fetch(`/signature/${documentId}/otp/${hashDocument}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Invit-Token': token,
        },
        body: JSON.stringify({
            document_id: documentId,
            user_id: documentData.currentUser.id
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Code OTP envoyé, affichage de la modale');
            showOTPModal();
        } else {
            console.error('Erreur lors de la demande OTP:', data.error);
            alert('Erreur lors de la demande de code OTP: ' + data.error);
            // Réactiver le bouton en cas d'erreur
            const signButton = document.getElementById('btn-sign');
            if (signButton) {
                signButton.disabled = false;
                signButton.innerHTML = '<i class="fas fa-pen"></i> Procéder à la signature';
            }
        }
    })
    .catch(error => {
        console.error('Erreur réseau:', error);
        alert('Erreur de connexion lors de la demande de code OTP');
        // Réactiver le bouton en cas d'erreur
        const signButton = document.getElementById('btn-sign');
        if (signButton) {
            signButton.disabled = false;
            signButton.innerHTML = '<i class="fas fa-pen"></i> Procéder à la signature';
        }
    });
}

function showOTPModal() {
    // Utiliser la modale existante
    const modal = document.getElementById('signatureModal');
    const modalTitle = document.getElementById('signatureModalLabel');
    const modalBody = modal.querySelector('.modal-body');
    const modalFooter = modal.querySelector('.modal-footer');
    
    modalTitle.innerHTML = '<i class="fas fa-pen-fancy"></i> Signature électronique avec validation';
    
    modalBody.innerHTML = `
        <div class="alert alert-info">
            <i class="fas fa-envelope"></i>
            Un code de validation a été envoyé à votre adresse e-mail.
            Tracez votre signature ci-dessous ET saisissez le code reçu.
        </div>
        
        <!-- Canvas de signature -->
        <div class="mb-4">
            <label class="form-label">Tracez votre signature :</label>
            <div class="signature-canvas-container text-center">
                <canvas id="signature-canvas" width="600" height="200"></canvas>
            </div>
            <div class="text-center mt-2">
                <button type="button" id="clear-signature" class="btn btn-outline-secondary btn-sm me-2">
                    <i class="fas fa-eraser"></i> Effacer
                </button>
                <button type="button" id="undo-signature" class="btn btn-outline-warning btn-sm">
                    <i class="fas fa-undo"></i> Annuler
                </button>
            </div>
        </div>
        
        <!-- Code OTP -->
        <div class="mb-3">
            <label for="otp-code" class="form-label">Code de validation :</label>
            <input type="text" id="otp-code" class="form-control text-center" 
                   placeholder="______" maxlength="6" 
                   style="font-size: 1.2em; letter-spacing: 0.4em;">
        </div>
    `;
    
    modalFooter.innerHTML = `
        <button type="button" id="btn-validate-signature" class="btn btn-success btn-lg" disabled>
            <i class="fas fa-check"></i> Valider la signature
        </button>
    `;
    
    // Afficher la modale
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Initialiser le SignaturePad après affichage de la modale
    setTimeout(() => {
        initializeSignaturePad();
        setupModalEventListeners();
    }, 300);
}

function initializeSignaturePad() {
    const canvas = document.getElementById('signature-canvas');
    if (!canvas) return;
    
    signaturePad = new SignaturePad(canvas, {
        backgroundColor: 'rgba(255, 255, 255, 1)',
        penColor: 'rgb(0, 0, 0)',
        minWidth: 1,
        maxWidth: 3,
        throttle: 0, // Pas de throttle pour capturer tous les points
        minDistance: 0 // Pas de distance minimale pour précision maximale
    });
    
    // Ajouter la capture haute précision
    setupHighPrecisionCapture(canvas);
    
    // Redimensionner le canvas
    resizeSignatureCanvas();
}

function setupHighPrecisionCapture(canvas) {
    let isDrawing = false;
    
    // Fonctions utilitaires
    function getCoordinates(event) {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        
        let clientX, clientY;
        if (event.touches && event.touches.length > 0) {
            clientX = event.touches[0].clientX;
            clientY = event.touches[0].clientY;
        } else {
            clientX = event.clientX;
            clientY = event.clientY;
        }
        
        return {
            x: Math.round((clientX - rect.left) * scaleX * 100) / 100, // Précision 0.01
            y: Math.round((clientY - rect.top) * scaleY * 100) / 100,  // Précision 0.01
            timestamp: performance.now(),
            pressure: event.pressure || 0.5
        };
    }
    
    function startStroke(event) {
        event.preventDefault();
        isDrawing = true;
        
        const coords = getCoordinates(event);
        customSignatureData.currentStroke = {
            id: Date.now() + Math.random(),
            startTime: coords.timestamp,
            points: [coords]
        };
    }
    
    function addPoint(event) {
        if (!isDrawing || !customSignatureData.currentStroke) return;
        
        event.preventDefault();
        const coords = getCoordinates(event);
        
        // Ajouter le point à la précision 0.01
        customSignatureData.currentStroke.points.push(coords);
    }
    
    function endStroke(event) {
        if (!isDrawing || !customSignatureData.currentStroke) return;
        
        event.preventDefault();
        isDrawing = false;
        
        const coords = getCoordinates(event);
        customSignatureData.currentStroke.points.push(coords);
        customSignatureData.currentStroke.endTime = coords.timestamp;
        
        // Ajouter le trait complet aux données
        customSignatureData.strokes.push(customSignatureData.currentStroke);
        customSignatureData.currentStroke = null;
        
        console.log('Fin de tracé. Total des traits:', customSignatureData.strokes.length);
        
        // Déclencher la validation
        setTimeout(checkValidation, 10);
    }
    
    // Event listeners souris
    canvas.addEventListener('mousedown', startStroke);
    canvas.addEventListener('mousemove', addPoint);
    canvas.addEventListener('mouseup', endStroke);
    canvas.addEventListener('mouseleave', endStroke);
    
    // Event listeners tactiles
    canvas.addEventListener('touchstart', startStroke);
    canvas.addEventListener('touchmove', addPoint);
    canvas.addEventListener('touchend', endStroke);
    canvas.addEventListener('touchcancel', endStroke);
}

function generateSVGFromStrokes(strokes) {
    if (!strokes || strokes.length === 0) return '';
    
    const canvas = document.getElementById('signature-canvas');
    const width = canvas.width;
    const height = canvas.height;
    
    let svgPaths = '';
    
    strokes.forEach(stroke => {
        if (stroke.points.length < 2) return;
        
        let pathData = `M ${stroke.points[0].x} ${stroke.points[0].y}`;
        
        for (let i = 1; i < stroke.points.length; i++) {
            pathData += ` L ${stroke.points[i].x} ${stroke.points[i].y}`;
        }
        
        svgPaths += `<path d="${pathData}" stroke="black" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`;
    });
    
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
        ${svgPaths}
    </svg>`;
    
    return svg;
}

function clearCustomSignature() {
    customSignatureData = {
        strokes: [],
        currentStroke: null,
        precision: 0.01
    };
    console.log('Signature effacée');
}

function undoLastStroke() {
    if (customSignatureData.strokes.length > 0) {
        customSignatureData.strokes.pop();
        console.log('Dernier trait annulé. Traits restants:', customSignatureData.strokes.length);
        // Redessiner le SignaturePad
        redrawSignaturePad();
    }
}

function redrawSignaturePad() {
    if (!signaturePad) return;
    
    signaturePad.clear();
    
    // Redessiner à partir des données customSignatureData
    customSignatureData.strokes.forEach(stroke => {
        if (stroke.points.length > 0) {
            const ctx = signaturePad._ctx;
            ctx.beginPath();
            ctx.moveTo(stroke.points[0].x, stroke.points[0].y);
            
            for (let i = 1; i < stroke.points.length; i++) {
                ctx.lineTo(stroke.points[i].x, stroke.points[i].y);
            }
            
            ctx.strokeStyle = 'rgb(0, 0, 0)';
            ctx.lineWidth = 2;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            ctx.stroke();
        }
    });
}

function resizeSignatureCanvas() {
    const canvas = document.getElementById('signature-canvas');
    if (!canvas || !signaturePad) return;
    
    const ratio = Math.max(window.devicePixelRatio || 1, 1);
    const rect = canvas.getBoundingClientRect();
    
    canvas.width = rect.width * ratio;
    canvas.height = rect.height * ratio;
    canvas.getContext('2d').scale(ratio, ratio);
    
    signaturePad.clear();
}

function setupModalEventListeners() {
    // Event listeners pour la modale
    const otpField = document.getElementById('otp-code');
    const validateBtn = document.getElementById('btn-validate-signature');
    const clearBtn = document.getElementById('clear-signature');
    const undoBtn = document.getElementById('undo-signature');
    
    // Validation en temps réel
    function checkValidation() {
        const hasSignature = signaturePad && !signaturePad.isEmpty();
        const hasHighPrecisionData = customSignatureData && customSignatureData.strokes.length > 0;
        const hasValidOTP = otpField.value.length === 6 && /^\d{6}$/.test(otpField.value);
        
        // La signature est valide si on a soit les données SignaturePad soit les données haute précision
        const signatureValid = hasSignature || hasHighPrecisionData;
        
        validateBtn.disabled = !(signatureValid && hasValidOTP);
        
        console.log('Validation état:', {
            hasSignature: hasSignature,
            hasHighPrecisionData: hasHighPrecisionData,
            hasValidOTP: hasValidOTP,
            buttonDisabled: validateBtn.disabled
        });
    }
    
    // Event listeners
    otpField.addEventListener('input', checkValidation);
    
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            signaturePad.clear();
            clearCustomSignature();
            checkValidation();
        });
    }
    
    if (undoBtn) {
        undoBtn.addEventListener('click', function() {
            undoLastStroke();
            checkValidation();
        });
    }
    
    if (signaturePad) {
        signaturePad.addEventListener('endStroke', checkValidation);
    }
    
    validateBtn.addEventListener('click', function() {
        validateSignatureWithOTP(otpField.value);
    });
    
    // Focus sur le champ OTP
    setTimeout(() => otpField.focus(), 100);
}

function validateSignatureWithOTP(otpCode) {
    console.log('Validation de la signature avec le code OTP:', otpCode);
    
    if (!signaturePad || signaturePad.isEmpty()) {
        alert('Veuillez tracer votre signature avant de valider');
        return;
    }
    
    const validateBtn = document.getElementById('btn-validate-signature');
    validateBtn.disabled = true;
    validateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Validation...';
    
    // Générer le hash de la signature
    const signatureDataURL = signaturePad.toDataURL();
    const signature_hash = CryptoJS.SHA256(signatureDataURL).toString();
    
    // Obtenir les informations du navigateur
    const user_agent = navigator.userAgent;
    
    // Récupérer les données de signature depuis SignaturePad
    const signaturePadData = signaturePad.toData();
    
    // Générer le SVG à partir des données de SignaturePad (toujours disponibles)
    let svg_graph = signaturePad.toSVG();
    
    console.log('Données SignaturePad:', {
        strokeCount: signaturePadData.length,
        customStrokeCount: customSignatureData.strokes.length,
        svgLength: svg_graph.length
    });
    
    // Si customSignatureData est vide, le remplir avec les données de SignaturePad
    if (customSignatureData.strokes.length === 0 && signaturePadData.length > 0) {
        console.log('Conversion des données SignaturePad vers customSignatureData');
        customSignatureData.strokes = signaturePadData.map((stroke, index) => ({
            id: Date.now() + index,
            startTime: performance.now(),
            endTime: performance.now(),
            points: stroke.points.map(point => ({
                x: point.x,
                y: point.y,
                timestamp: point.time,
                pressure: point.pressure || 0.5
            }))
        }));
    }
    
    console.log('SVG généré (longueur):', svg_graph.length, 'premiers caractères:', svg_graph.substring(0, 200));
    
    // Préparer les données JSON avec toutes les informations
    const data_graph = JSON.stringify({
        strokes: customSignatureData.strokes,
        precision: customSignatureData.precision,
        captureMethod: 'high-precision',
        timestamp: new Date().toISOString(),
        signaturePadData: signaturePad.toData(), // Données SignaturePad pour compatibilité
        metadata: {
            browser: navigator.userAgent,
            platform: navigator.userAgentData?.platform || 'unknown',
            language: navigator.language,
            screen: {
                width: screen.width,
                height: screen.height,
                pixelRatio: window.devicePixelRatio
            },
            canvas: {
                actualWidth: document.getElementById('signature-canvas').width,
                actualHeight: document.getElementById('signature-canvas').height,
                displayWidth: document.getElementById('signature-canvas').offsetWidth,
                displayHeight: document.getElementById('signature-canvas').offsetHeight
            }
        }
    });
    
    // Obtenir les dimensions du canvas
    const canvas = document.getElementById('signature-canvas');
    const largeur_graph = canvas.width;
    const hauteur_graph = canvas.height;
    
    console.log('Données de signature à envoyer:', {
        signature_hash: signature_hash,
        user_agent: user_agent.substring(0, 50) + '...',
        svg_graph: svg_graph.substring(0, 100) + '...',
        data_graph_size: data_graph.length + ' caractères',
        largeur_graph: largeur_graph,
        hauteur_graph: hauteur_graph,
        totalStrokes: customSignatureData.strokes.length,
        totalPoints: customSignatureData.strokes.reduce((acc, stroke) => acc + stroke.points.length, 0)
    });
    
    fetch(`/signature/signer/${documentId}/${hashDocument}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Invit-Token': token,
        },
        body: JSON.stringify({
            document_id: documentData.id,
            user_id: documentData.currentUser.id,
            otp_code: otpCode,
            signature_hash: signature_hash,
            user_agent: user_agent,
            svg_graph: svg_graph,
            data_graph: data_graph,
            largeur_graph: largeur_graph,
            hauteur_graph: hauteur_graph,
            // Données de compatibilité
            signature_data: {
                dataURL: signatureDataURL,
                svg: signaturePad.toSVG(),
                points: signaturePad.toData()
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Signature validée avec succès');
            
            // Vérifier si tous les signataires ont signé
            if (data.all_signed) {
                // Tous les signataires ont signé, créer le document final
                alert('Toutes les signatures ont été collectées ! Le document final est en cours de création...');
                
                // Rediriger vers la route de création du document final
                fetch(`/signature/creer/${data.document_id}/${data.hash_document}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(finalData => {
                    if (finalData.success) {
                        alert('Document final créé avec succès ! ' + finalData.message);
                        window.location.href = '/ea?success_message=' + encodeURIComponent(finalData.message);
                    } else {
                        console.error('Erreur lors de la création du document final:', finalData.message);
                        alert('Erreur lors de la création du document final: ' + finalData.message);
                        window.location.href = '/ea?error_message=' + encodeURIComponent(finalData.message);
                    }
                })
                .catch(error => {
                    console.error('Erreur lors de la création du document final:', error);
                    alert('Erreur lors de la création du document final');
                    window.location.href = '/ea';
                });
            } else {
                // Il reste des signatures en attente
                alert('Signature validée avec succès ! En attente des autres signataires.');
                window.location.href = '/ea?success_message=' + encodeURIComponent(data.message);
            }
        } else {
            console.error('Erreur lors de la validation:', data.message);
            alert('Code de validation incorrect: ' + data.message);
            // Réactiver le bouton
            validateBtn.disabled = false;
            validateBtn.innerHTML = '<i class="fas fa-check"></i> Valider la signature';
        }
    })
    .catch(error => {
        console.error('Erreur réseau:', error);
        alert('Erreur de connexion lors de la validation');
        // Réactiver le bouton
        validateBtn.disabled = false;
        validateBtn.innerHTML = '<i class="fas fa-check"></i> Valider la signature';
    });
}

// ===========================================
// STYLES CSS DYNAMIQUES
// ===========================================

const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .signature-rectangle {
        transition: all 0.2s ease;
    }
    
    .signature-rectangle:hover {
        background-color: rgba(25, 135, 84, 0.4) !important;
        transform: scale(1.05);
    }
    
    #signature-canvas {
        border: 2px solid #dee2e6;
        border-radius: 0.375rem;
        cursor: crosshair;
        background-color: #fff;
    }
    
    .signature-canvas-container {
        border: 1px solid #ced4da;
        border-radius: 0.375rem;
        padding: 10px;
        background-color: #f8f9fa;
    }
    
    #otp-code {
        text-transform: uppercase;
        font-family: 'Courier New', monospace;
    }
`;
document.head.appendChild(style);