/**
 * Signatures - Fonctions communes
 * Partagées entre signature_make.html et signature_do.html
 */

// Variables globales communes
let pdfDocument = null;
let pdfScale = 1.5;

// ===========================================
// FONCTIONS PDF.JS COMMUNES
// ===========================================

/**
 * Initialise le chargement d'un PDF
 * @param {string} filename - Nom du fichier PDF
 * @param {HTMLElement} loader - Élément loader
 * @param {HTMLElement} container - Conteneur PDF
 * @param {Function} onComplete - Callback à exécuter après chargement complet
 */
function initializePDFViewer(filename, loader, container, onComplete = null, tempDir = false) {
    loader.style.display = "flex";
    container.style.display = "none";

    const url = `/signature/download/${filename}?temp_dir=${tempDir}`;
    
    const loadingTask = pdfjsLib.getDocument(url);
    loadingTask.promise.then(function(pdf) {
        pdfDocument = pdf;
        const numPages = pdf.numPages;
        
        // Vider le conteneur
        container.innerHTML = '';
        
        // Compteur pour suivre les pages rendues
        let renderedPages = 0;
        
        // Rendre toutes les pages
        for (let pageNum = 1; pageNum <= numPages; pageNum++) {
            renderPDFPage(pdf, pageNum, numPages, loader, container, function() {
                renderedPages++;
                // Appeler le callback seulement quand toutes les pages sont rendues
                if (renderedPages === numPages && onComplete && typeof onComplete === 'function') {
                    onComplete();
                }
            });
        }
        
    }, function(reason) {
        console.error('Erreur lors du chargement du PDF:', reason);
    });
}

/**
 * Rend une page PDF
 * @param {Object} pdf - Document PDF
 * @param {number} pageNum - Numéro de la page
 * @param {number} numPages - Nombre total de pages
 * @param {HTMLElement} loader - Élément loader
 * @param {HTMLElement} container - Conteneur PDF
 * @param {Function} onComplete - Callback à exécuter après chargement complet
 */
function renderPDFPage(pdf, pageNum, numPages, loader, container, onComplete) {
    pdf.getPage(pageNum).then(function(page) {
        const viewport = page.getViewport({ scale: pdfScale });

        // Créer un conteneur pour cette page
        const pageDiv = document.createElement('div');
        pageDiv.className = 'pdf-page';
        pageDiv.style.marginBottom = '10px';
        pageDiv.style.position = 'relative';
        pageDiv.setAttribute('data-page-number', pageNum);
        
        // Préparation du canvas
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        canvas.setAttribute('data-page-number', pageNum);
        
        pageDiv.appendChild(canvas);
        container.appendChild(pageDiv);

        // Rendu de la page
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        
        page.render(renderContext).promise.then(function() {
            console.log(`Page ${pageNum} rendue`);
            
            // Masquer le loader après la première page pour un affichage progressif
            if (pageNum === 1) {
                loader.style.display = "none";
                container.style.display = "block";
            }
            
            // Exécuter le callback pour cette page
            if (onComplete && typeof onComplete === 'function') {
                onComplete();
            }
        });
    });
}

// ===========================================
// FONCTIONS UTILITAIRES
// ===========================================

/**
 * Détecte le type d'input utilisé
 * @returns {string} Type d'input: 'touch', 'pointer', ou 'mouse'
 */
function detectInputType() {
    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
        return 'touch';
    } else if (window.PointerEvent) {
        return 'pointer';
    } else {
        return 'mouse';
    }
}

/**
 * Génère un SVG à partir des données de signature
 * @param {Object} signatureData - Données de signature au format JSON
 * @returns {string} Code SVG
 */
function generateSVGFromData(signatureData) {
    let svgPaths = [];
    
    signatureData.strokes.forEach(stroke => {
        if (stroke.points.length === 0) return;
        
        let pathD = `M${stroke.points[0].x},${stroke.points[0].y}`;
        
        for (let i = 1; i < stroke.points.length; i++) {
            const point = stroke.points[i];
            if (i < stroke.points.length - 1) {
                const nextPoint = stroke.points[i + 1];
                const cp_x = (point.x + nextPoint.x) / 2;
                const cp_y = (point.y + nextPoint.y) / 2;
                pathD += ` Q${point.x},${point.y} ${cp_x},${cp_y}`;
            } else {
                pathD += ` L${point.x},${point.y}`;
            }
        }
        
        svgPaths.push(`<path d="${pathD}" stroke="${stroke.color}" stroke-width="${stroke.width}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`);
    });
    
    return `<svg width="${signatureData.bounds.width}" height="${signatureData.bounds.height}" xmlns="http://www.w3.org/2000/svg">${svgPaths.join('')}</svg>`;
}

/**
 * Convertit les coordonnées pixels en points PDF
 * @param {number} pixels - Valeur en pixels
 * @param {number} scale - Échelle d'affichage
 * @returns {number} Valeur en points PDF
 */
function pixelsToPdfPoints(pixels, scale) {
    return pixels / scale * 72 / 96; // 96 DPI par défaut
}

/**
 * Convertit les points PDF en pixels
 * @param {number} points - Valeur en points PDF
 * @param {number} scale - Échelle d'affichage
 * @returns {number} Valeur en pixels
 */
function pdfPointsToPixels(points, scale) {
    return points * scale * 96 / 72;
}

/**
 * Formate une date pour l'affichage
 * @param {Date|string} date - Date à formater
 * @returns {string} Date formatée
 */
function formatDateTime(date) {
    const d = new Date(date);
    return d.toLocaleDateString('fr-FR') + ' à ' + d.toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Génère un identifiant unique
 * @returns {string} Identifiant unique
 */
function generateUniqueId() {
    return 'id-' + Math.random().toString(36).substr(2, 9) + '-' + Date.now();
}

/**
 * Valide une adresse email
 * @param {string} email - Email à valider
 * @returns {boolean} True si valide
 */
function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

/**
 * Affiche une notification toast
 * @param {string} message - Message à afficher
 * @param {string} type - Type: 'success', 'error', 'warning', 'info'
 */
function showNotification(message, type = 'info') {
    // Implémentation simple, peut être améliorée avec une librairie toast
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';
    
    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-suppression après 5 secondes
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// ===========================================
// VALIDATION COMMUNES
// ===========================================

/**
 * Valide les données d'un document
 * @param {Object} documentData - Données du document
 * @returns {Object} Résultat de validation {isValid: boolean, errors: string[]}
 */
function validateDocumentData(documentData) {
    const errors = [];
    
    if (!documentData.id) {
        errors.push('ID du document manquant');
    }
    
    if (!documentData.filename || documentData.filename.trim() === '') {
        errors.push('Nom de fichier manquant');
    }
    
    if (!documentData.name || documentData.name.trim() === '') {
        errors.push('Nom du document manquant');
    }
    
    return {
        isValid: errors.length === 0,
        errors: errors
    };
}

/**
 * Valide les données de signature
 * @param {Object} signatureData - Données de signature
 * @returns {Object} Résultat de validation {isValid: boolean, errors: string[]}
 */
function validateSignatureData(signatureData) {
    const errors = [];
    
    if (!signatureData.strokes || signatureData.strokes.length === 0) {
        errors.push('Aucun tracé de signature détecté');
    }
    
    if (!signatureData.timestamp) {
        errors.push('Timestamp de signature manquant');
    }
    
    if (signatureData.strokes) {
        signatureData.strokes.forEach((stroke, index) => {
            if (!stroke.points || stroke.points.length === 0) {
                errors.push(`Tracé ${index + 1} vide`);
            }
        });
    }
    
    return {
        isValid: errors.length === 0,
        errors: errors
    };
}
