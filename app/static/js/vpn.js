(() => {
    'use strict';

    const workspace = document.getElementById('vpn-workspace');
    if (!workspace) return;

    const message = document.getElementById('vpn-message');
    const leaseForm = document.getElementById('lease-form');
    const deviceForm = document.getElementById('device-form');
    const profileSelect = document.getElementById('lease-profile');
    const deviceSelect = document.getElementById('lease-device');
    const hoursInput = document.getElementById('duration-hours');
    const minutesInput = document.getElementById('duration-minutes');
    const leasePassword = document.getElementById('lease-passphrase');
    const downloadDialog = document.getElementById('download-dialog');
    const downloadForm = document.getElementById('download-form');
    const downloadPassword = document.getElementById('download-passphrase');
    const downloadError = document.getElementById('download-error');
    const csrf = document.querySelector('meta[name="csrf-token"]').content;
    let data = { devices: [], profiles: [], leases: [] };
    let downloadLease = null;

    function showMessage(text, error = false) {
        message.textContent = text;
        message.classList.toggle('is-error', error);
        message.hidden = !text;
    }

    async function request(url, body) {
        let response;
        try {
            response = await fetch(url, {
                method: body === undefined ? 'GET' : 'POST',
                credentials: 'same-origin',
                cache: 'no-store',
                headers: body === undefined ? {} : { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                body: body === undefined ? undefined : JSON.stringify(body),
            });
        } catch {
            throw new Error('Connexion interrompue. Vérifiez l’état avant de réessayer.');
        }
        const result = await response.json().catch(() => null);
        if (!response.ok || !result) {
            const text = result?.error || result?.message || 'Service VPN indisponible.';
            throw new Error(result?.lease_id ? `${text} Bail n° ${result.lease_id}.` : text);
        }
        return result;
    }

    function encode(bytes) {
        return btoa(String.fromCharCode(...new Uint8Array(bytes)));
    }

    function decode(text) {
        return Uint8Array.from(atob(text), character => character.charCodeAt(0));
    }

    function fromUrl(text) {
        return text.replaceAll('-', '+').replaceAll('_', '/');
    }

    function toUrl(text) {
        return text.replaceAll('+', '-').replaceAll('/', '_').replaceAll('=', '');
    }

    function storageKey(publicKey) {
        return `intranet.vpn.${workspace.dataset.userId}.${publicKey}`;
    }

    function hasKey(publicKey) {
        try {
            return Boolean(publicKey && localStorage.getItem(storageKey(publicKey)));
        } catch {
            return false;
        }
    }

    async function encryptionKey(password, salt) {
        const material = await crypto.subtle.importKey(
            'raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveKey'],
        );
        return crypto.subtle.deriveKey(
            { name: 'PBKDF2', hash: 'SHA-256', salt, iterations: 600000 },
            material, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt'],
        );
    }

    async function createLocalKey(password) {
        if (!window.isSecureContext || !crypto.subtle || !workspace.dataset.userId) {
            throw new Error('La génération de clés nécessite une connexion HTTPS et un navigateur compatible.');
        }
        let pair;
        try {
            pair = await crypto.subtle.generateKey({ name: 'X25519' }, true, ['deriveBits']);
        } catch {
            throw new Error('Ce navigateur ne prend pas en charge les clés WireGuard X25519.');
        }
        const [publicJwk, privateJwk] = await Promise.all([
            crypto.subtle.exportKey('jwk', pair.publicKey),
            crypto.subtle.exportKey('jwk', pair.privateKey),
        ]);
        const publicKey = encode(decode(fromUrl(publicJwk.x)));
        const privateKey = decode(fromUrl(privateJwk.d));
        const salt = crypto.getRandomValues(new Uint8Array(16));
        const iv = crypto.getRandomValues(new Uint8Array(12));
        const key = await encryptionKey(password, salt);
        const encrypted = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, privateKey);
        privateKey.fill(0);
        try {
            localStorage.setItem(storageKey(publicKey), JSON.stringify({
                version: 1, salt: encode(salt), iv: encode(iv), ciphertext: encode(encrypted),
            }));
        } catch {
            throw new Error('Le stockage local est indisponible. Le terminal n’a pas été créé.');
        }
        return publicKey;
    }

    async function unlockKey(publicKey, password) {
        let record;
        try {
            record = JSON.parse(localStorage.getItem(storageKey(publicKey)) || 'null');
        } catch {
            record = null;
        }
        if (!record || record.version !== 1) {
            throw new Error('Clé locale indisponible. Créez un nouveau terminal dans ce navigateur.');
        }
        let privateBytes;
        try {
            const key = await encryptionKey(password, decode(record.salt));
            const decrypted = await crypto.subtle.decrypt(
                { name: 'AES-GCM', iv: decode(record.iv) }, key, decode(record.ciphertext),
            );
            privateBytes = new Uint8Array(decrypted);
            if (privateBytes.length !== 32) throw new Error('Invalid key');
        } catch {
            throw new Error('Phrase secrète incorrecte ou clé locale illisible.');
        }
        try {
            await verifyPrivateKey(publicKey, privateBytes);
        } catch (error) {
            privateBytes.fill(0);
            throw error;
        }
        return privateBytes;
    }

    async function verifyPrivateKey(publicKey, privateBytes) {
        const privateKey = encode(privateBytes);
        const key = await crypto.subtle.importKey('jwk', {
            kty: 'OKP', crv: 'X25519', d: toUrl(privateKey),
            x: toUrl(publicKey), ext: false, key_ops: ['deriveBits'],
        }, { name: 'X25519' }, false, ['deriveBits']);
        const basepoint = new Uint8Array(32);
        basepoint[0] = 9;
        const base = await crypto.subtle.importKey('raw', basepoint, { name: 'X25519' }, false, []);
        const derived = await crypto.subtle.deriveBits({ name: 'X25519', public: base }, key, 256);
        if (encode(derived) !== publicKey) {
            throw new Error('La clé locale ne correspond pas à ce terminal.');
        }
    }

    async function downloadConfiguration(lease, privateBytes) {
        const configuration = await request(`${workspace.dataset.leasesUrl}/${lease.id}/configuration`);
        if (typeof configuration.device_public_key !== 'string'
                || typeof configuration.configuration_template !== 'string'
                || configuration.configuration_template.split('REPLACE_WITH_LOCAL_PRIVATE_KEY').length !== 2) {
            throw new Error('Configuration VPN reçue invalide.');
        }
        await verifyPrivateKey(configuration.device_public_key, privateBytes);
        const privateKey = encode(privateBytes);
        const content = configuration.configuration_template.replace('REPLACE_WITH_LOCAL_PRIVATE_KEY', privateKey);
        const url = URL.createObjectURL(new Blob([content], { type: 'text/plain;charset=utf-8' }));
        const link = document.createElement('a');
        link.href = url;
        link.download = `wireguard-${lease.id}.conf`;
        document.body.append(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }

    function durationSeconds(value) {
        if (typeof value !== 'string' || value.length > 100) return null;
        const parts = [...value.matchAll(/(\d+)([dhms])/g)];
        if (!parts.length || parts.map(part => part[0]).join('') !== value) return null;
        const seconds = parts.reduce((total, part) => total + Number(part[1]) * {
            d: 86400, h: 3600, m: 60, s: 1,
        }[part[2]], 0);
        return Number.isSafeInteger(seconds) && seconds > 0 ? seconds : null;
    }

    function setDuration() {
        const profile = data.profiles.find(item => String(item.id) === profileSelect.value);
        const defaultSeconds = durationSeconds(profile?.policy?.default_duration);
        const maximum = durationSeconds(profile?.policy?.maximum_duration);
        const available = defaultSeconds && maximum && defaultSeconds % 60 === 0 && maximum >= 60;
        document.getElementById('duration-limit').textContent = available
            ? `Maximum : ${profile.policy.maximum_duration}`
            : 'Durée du profil indisponible ou non exprimable en minutes.';
        if (available) {
            const totalMinutes = defaultSeconds / 60;
            hoursInput.value = String(Math.floor(totalMinutes / 60));
            minutesInput.value = String(totalMinutes % 60);
        }
        leaseForm.querySelector('button[type="submit"]').disabled = !available || !deviceSelect.value;
    }

    function element(tag, className, text) {
        const item = document.createElement(tag);
        if (className) item.className = className;
        if (text !== undefined) item.textContent = text;
        return item;
    }

    function action(icon, label, callback, danger = false) {
        const button = element('button', `btn btn-sm ${danger ? 'btn-outline-danger' : 'btn-outline-primary'}`);
        button.type = 'button';
        button.title = label;
        button.setAttribute('aria-label', label);
        const symbol = element('i', `bi ${icon}`);
        symbol.setAttribute('aria-hidden', 'true');
        button.append(symbol);
        button.addEventListener('click', async () => {
            button.disabled = true;
            try { await callback(); } finally { button.disabled = false; }
        });
        return button;
    }

    function formatDate(value) {
        const date = new Date(value);
        return value && !Number.isNaN(date.getTime()) ? new Intl.DateTimeFormat('fr-FR', {
            dateStyle: 'medium', timeStyle: 'short',
        }).format(date) : '—';
    }

    function render() {
        const activeDevices = data.devices.filter(device => !device.revoked_at);
        profileSelect.replaceChildren();
        deviceSelect.replaceChildren();
        for (const profile of data.profiles) {
            const option = element('option', '', profile.name);
            option.value = String(profile.id);
            profileSelect.append(option);
        }
        for (const device of activeDevices) {
            const option = element('option', '', `${device.name}${hasKey(device.public_key) ? '' : ' (clé indisponible)'}`);
            option.value = String(device.id);
            deviceSelect.append(option);
        }
        profileSelect.disabled = !data.profiles.length;
        deviceSelect.disabled = !activeDevices.length;
        document.querySelector('#device-form button[type="submit"]').disabled = false;
        setDuration();

        const devicesList = document.getElementById('devices-list');
        devicesList.replaceChildren();
        if (!activeDevices.length) devicesList.append(element('p', 'vpn-muted', 'Aucun terminal enregistré.'));
        for (const device of activeDevices) {
            const row = element('div', 'vpn-item');
            const main = element('div', 'vpn-item-main');
            main.append(element('div', 'vpn-item-title', device.name));
            main.append(element('div', 'vpn-item-meta', hasKey(device.public_key)
                ? `Ajouté le ${formatDate(device.created_at)} · Clé disponible sur ce navigateur`
                : 'Clé indisponible sur ce navigateur'));
            const actions = element('div', 'vpn-actions');
            actions.append(action('bi-trash', `Supprimer ${device.name}`, async () => {
                if (!window.confirm(`Supprimer « ${device.name} » ? Ses baux seront révoqués.`)) return;
                try {
                    await request(`${workspace.dataset.devicesUrl}/${device.id}/delete`, {});
                    try { localStorage.removeItem(storageKey(device.public_key)); } catch {}
                    showMessage('Terminal supprimé et baux associés révoqués.');
                    await refresh();
                } catch (error) { showMessage(error.message, true); }
            }, true));
            row.append(main, actions);
            devicesList.append(row);
        }

        const leasesList = document.getElementById('leases-list');
        leasesList.replaceChildren();
        if (!data.leases.length) leasesList.append(element('p', 'vpn-muted', 'Aucun bail créé.'));
        const labels = { active: 'Actif', expired: 'Expiré', revoked: 'Révoqué', pending: 'En cours', failed: 'Échec' };
        for (const lease of data.leases) {
            const device = data.devices.find(item => item.id === lease.device_id);
            const profile = data.profiles.find(item => item.id === lease.profile_id);
            const row = element('div', 'vpn-item');
            const main = element('div', 'vpn-item-main');
            const title = element('div', 'vpn-item-title');
            title.append(element('span', '', `${profile?.name || `Profil n° ${lease.profile_id}`} · ${device?.name || `Terminal n° ${lease.device_id}`}`));
            title.append(element('span', `vpn-status vpn-status-${lease.status}`, labels[lease.status] || 'Inconnu'));
            main.append(title, element('div', 'vpn-item-meta', `Créé le ${formatDate(lease.created_at)} · Fin : ${formatDate(lease.ended_at)}`));
            const actions = element('div', 'vpn-actions');
            if (lease.status === 'active') {
                actions.append(action('bi-file-earmark-arrow-down', 'Télécharger la configuration', () => {
                    if (!device || !hasKey(device.public_key)) {
                        showMessage('Clé locale indisponible. Créez un nouveau terminal dans ce navigateur.', true);
                        return;
                    }
                    downloadLease = lease;
                    downloadError.textContent = '';
                    downloadPassword.value = '';
                    downloadDialog.showModal();
                }));
                actions.append(action('bi-x-circle', 'Révoquer le bail', async () => {
                    if (!window.confirm('Révoquer ce bail VPN ?')) return;
                    try {
                        await request(`${workspace.dataset.leasesUrl}/${lease.id}/revoke`, {});
                        showMessage('Bail révoqué.');
                        await refresh();
                    } catch (error) { showMessage(error.message, true); }
                }, true));
            }
            row.append(main, actions);
            leasesList.append(row);
        }
    }

    async function refresh() {
        data = await request(workspace.dataset.stateUrl);
        if (!Array.isArray(data.devices) || !Array.isArray(data.profiles) || !Array.isArray(data.leases)) {
            throw new Error('Réponse VPN invalide.');
        }
        render();
    }

    profileSelect.addEventListener('change', setDuration);
    deviceSelect.addEventListener('change', setDuration);
    document.getElementById('refresh-vpn').addEventListener('click', async event => {
        const button = event.currentTarget;
        button.disabled = true;
        try {
            await refresh();
            showMessage('État VPN actualisé.');
        } catch (error) {
            showMessage(error.message, true);
        } finally {
            button.disabled = false;
        }
    });

    deviceForm.addEventListener('submit', async event => {
        event.preventDefault();
        const password = document.getElementById('device-passphrase');
        const confirmPassword = document.getElementById('device-passphrase-confirm');
        if (password.value !== confirmPassword.value) {
            showMessage('Les phrases secrètes ne correspondent pas.', true);
            return;
        }
        const submit = deviceForm.querySelector('button[type="submit"]');
        submit.disabled = true;
        showMessage('Création du terminal en cours...');
        try {
            const publicKey = await createLocalKey(password.value);
            await request(workspace.dataset.devicesUrl, {
                name: document.getElementById('device-name').value.trim(), public_key: publicKey,
            });
            deviceForm.reset();
            document.getElementById('device-disclosure').open = false;
            showMessage('Terminal créé.');
            await refresh();
        } catch (error) {
            showMessage(error.message, true);
        } finally {
            password.value = '';
            confirmPassword.value = '';
            submit.disabled = false;
        }
    });

    leaseForm.addEventListener('submit', async event => {
        event.preventDefault();
        const device = data.devices.find(item => String(item.id) === deviceSelect.value);
        const profile = data.profiles.find(item => String(item.id) === profileSelect.value);
        const hours = Number(hoursInput.value);
        const minutes = Number(minutesInput.value);
        const total = hours * 60 + minutes;
        const maximum = durationSeconds(profile?.policy?.maximum_duration);
        if (!device || !profile || !Number.isSafeInteger(total) || total <= 0
                || !Number.isInteger(hours) || hours < 0 || !Number.isInteger(minutes)
                || minutes < 0 || minutes > 59 || !maximum || total * 60 > maximum) {
            showMessage('La durée doit être positive et ne pas dépasser le maximum du profil.', true);
            return;
        }
        const submit = leaseForm.querySelector('button[type="submit"]');
        submit.disabled = true;
        let privateBytes;
        try {
            showMessage('Déverrouillage du terminal...');
            privateBytes = await unlockKey(device.public_key, leasePassword.value);
            showMessage('Création du bail en cours...');
            const lease = await request(workspace.dataset.leasesUrl, {
                device_id: device.id, profile_id: profile.id, duration_minutes: total,
            });
            try {
                await downloadConfiguration(lease, privateBytes);
                showMessage('Bail créé et configuration téléchargée.');
            } catch (error) {
                showMessage(`Bail créé. Le téléchargement a échoué : ${error.message}`, true);
            }
            await refresh();
        } catch (error) {
            showMessage(error.message, true);
        } finally {
            if (privateBytes) privateBytes.fill(0);
            leasePassword.value = '';
            setDuration();
        }
    });

    document.getElementById('download-cancel').addEventListener('click', () => downloadDialog.close());
    downloadDialog.addEventListener('close', () => { downloadPassword.value = ''; downloadLease = null; });
    downloadForm.addEventListener('submit', async event => {
        event.preventDefault();
        const device = data.devices.find(item => item.id === downloadLease?.device_id);
        const submit = downloadForm.querySelector('button[type="submit"]');
        submit.disabled = true;
        let privateBytes;
        try {
            if (!device) throw new Error('Terminal indisponible.');
            privateBytes = await unlockKey(device.public_key, downloadPassword.value);
            await downloadConfiguration(downloadLease, privateBytes);
            downloadDialog.close();
            showMessage('Configuration téléchargée.');
        } catch (error) {
            downloadError.textContent = error.message;
        } finally {
            if (privateBytes) privateBytes.fill(0);
            downloadPassword.value = '';
            submit.disabled = false;
        }
    });

    refresh().catch(error => showMessage(error.message, true));
})();