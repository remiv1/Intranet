document.querySelectorAll('.vpn-rights-form').forEach((form) => {
    const toggle = form.querySelector('.vpn-toggle');
    const container = form.querySelector('.vpn-profiles');
    const loaded = form.querySelector('[name="vpn_profiles_loaded"]');
    const menu = form.querySelector('.vpn-profiles-menu');
    const button = form.querySelector('.vpn-profiles-button');
    const status = form.querySelector('.vpn-profiles-status');
    const rightsButton = form.querySelector('.rights-dropdown-button');
    const rightsCheckboxes = form.querySelectorAll('.rights-checkbox');
    let loading = false;
    let loadedRights = '';

    const selectedRights = () => Array.from(rightsCheckboxes)
        .filter((checkbox) => checkbox.checked)
        .map((checkbox) => checkbox.value)
        .join('');

    const updateRightsLabel = () => {
        const count = form.querySelectorAll('.rights-checkbox:checked').length;
        rightsButton.textContent = count
            ? `${count} droit${count > 1 ? 's' : ''} sélectionné${count > 1 ? 's' : ''}`
            : 'Sélectionner les droits';
    };

    const updateLabel = () => {
        const count = menu.querySelectorAll('[data-profile-id]').length;
        button.textContent = count
            ? `${count} profil${count > 1 ? 's' : ''} attribué${count > 1 ? 's' : ''}`
            : 'Aucun profil attribué';
    };

    const loadProfiles = async () => {
        const habilitation = selectedRights();
        if (loading || (loaded.value === '1' && loadedRights === habilitation)) return;
        loading = true;
        button.disabled = true;
        status.textContent = 'Chargement des profils...';
        try {
            const profilesUrl = new URL(form.dataset.profilesUrl, window.location.origin);
            profilesUrl.searchParams.set('habilitation', habilitation);
            const response = await fetch(profilesUrl, {credentials: 'same-origin'});
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Profils VPN indisponibles.');
            menu.replaceChildren();
            data.profiles.forEach((profile) => {
                const label = document.createElement('div');
                label.className = 'dropdown-item d-flex align-items-center gap-2';
                label.dataset.profileId = String(profile.id);
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'form-check-input m-0';
                checkbox.checked = data.selected.includes(profile.id);
                checkbox.disabled = true;
                label.append(checkbox, document.createTextNode(profile.name));
                menu.append(label);
            });
            loaded.value = '1';
            loadedRights = habilitation;
            button.disabled = !data.profiles.length;
            status.textContent = data.profiles.length
                ? (data.pending ? 'Synchronisation VPN en attente.' : 'Affectation automatique selon les droits.')
                : 'Aucun profil VPN ne correspond aux droits sélectionnés.';
            updateLabel();
        } catch (error) {
            status.textContent = error.message || 'Profils VPN indisponibles.';
            button.disabled = true;
        } finally {
            loading = false;
            if (toggle.checked && loadedRights !== selectedRights()) loadProfiles();
        }
    };

    const toggleProfiles = () => {
        container.hidden = !toggle.checked;
        if (toggle.checked) loadProfiles();
    };

    rightsCheckboxes.forEach((checkbox) => {
        if (checkbox === toggle) return;
        checkbox.addEventListener('change', () => {
            updateRightsLabel();
            toggleProfiles();
        });
    });
    toggle.addEventListener('change', () => {
        updateRightsLabel();
        toggleProfiles();
    });
    updateRightsLabel();
    form.closest('.modal').addEventListener('show.bs.modal', toggleProfiles);
});