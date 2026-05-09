# Architecture — Extranet + VPN éphémère sur Proxmox

## Vue d'ensemble

Système de provisioning VPN à la demande, avec accès différenciés par utilisateur, déployé sur un serveur Proxmox exposé en IPv6 natif (Orange Livebox).

---

## Infrastructure physique

```txt
[Livebox Orange]
      │
      │ IPv6 natif — pas de NAT, routage transparent
      │
[Serveur Proxmox — 4 ports RJ45]
      │
      ├── Port 1 → vmbr0 — LAN administration (réseau privé)
      ├── Port 2 → vmbr1 — Réseau exposé (VM Extranet + VM WireGuard)
      ├── Port 3 → vmbr2 — Réseau interne VMs (adresses ULA fd00::/8)
      └── Port 4 → Réservé (backup, stockage réseau)
```

---

## Adressage IPv6

| Ressource | Type d'adresse | Visible internet |
| --- | --- | --- |
| VM Extranet | IPv6 publique (préfixe Orange) | Oui — port 443 uniquement |
| VM WireGuard | IPv6 publique (préfixe Orange) | Oui — port UDP 51820 uniquement |
| VMs internes | IPv6 ULA `fd00::/8` | **Non** — non routable par définition |
| Administration Proxmox | IPv6 ULA | **Non** |

> Le préfixe Orange (`/56` ou `/60`) pouvant changer, un service DDNS compatible IPv6 (ex. Cloudflare) est recommandé pour les endpoints publics.

---

## Les deux VMs exposées

### VM Extranet

- **Rôle** : authentification, gestion des droits, provisioning des clés VPN
- **Stack** : Python + Flask (existant) + SQLAlchemy + APScheduler
- **Exposition** : HTTPS port 443 uniquement
- **Communication vers VM WireGuard** : API interne sur adresse ULA (non exposée)

### VM WireGuard

- **Rôle** : point d'entrée VPN unique, isolation des accès
- **Exposition** : UDP port 51820 uniquement
- **Gestion des peers** : micro-API Flask interne, accessible uniquement depuis la VM Extranet via ULA
- **Comportement** : silencieux aux paquets non authentifiés (invisible au scan sans clé valide)

---

## Flux de provisioning VPN

```txt
1. Utilisateur s'authentifie sur l'Extranet (auth Flask existante — rôles, anti-brute-force)
        │
2. L'Extranet détermine les VMs accessibles selon le rôle utilisateur
        │
3. Génération d'une paire de clés WireGuard éphémères (côté serveur)
        │
4. Enregistrement du peer sur la VM WireGuard via API interne ULA
   → wg set wg0 peer <PUBLIC_KEY> allowed-ips <IPs selon rôle>
        │
5. Génération du fichier .conf client + QR code optionnel
        │
6. Téléchargement par l'utilisateur
        │
7. Expiration automatique à minuit — purge des peers expirés
```

---

## Contrôle des accès par rôle

Les accès aux VMs sont définis par le champ `AllowedIPs` de WireGuard, mappé depuis les rôles Flask existants.

```python
VM_ACCESS_MAP = {
    "admin":      ["10.0.0.1/32", "10.0.0.2/32", "10.0.0.3/32"],  # Proxmox + toutes VMs
    "partenaire": ["10.0.0.2/32", "10.0.0.3/32"],                  # VM1 + VM2
    "client":     ["10.0.0.2/32"],                                  # VM1 uniquement
}
```

> `AllowedIPs` est appliqué à deux niveaux : dans le `.conf` client (ce que le client route) et dans la config peer serveur (ce que WireGuard accepte). Un troisième niveau de contrôle via `iptables` sur Proxmox constitue le filet de sécurité final.

---

## Cycle de vie des clés

| Événement | Action |
| --- | --- |
| Demande utilisateur | Génération paire de clés + enregistrement peer |
| Minuit (cron) | Purge de tous les peers expirés |
| Suppression manuelle | API DELETE sur la VM WireGuard |

```python
# Expiration à minuit
def get_expiry():
    today = datetime.utcnow().date()
    midnight = datetime.combine(today + timedelta(days=1), time(0, 0))
    return midnight
```

---

## Modèle de données — table à ajouter

```python
class VPNPeer(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("user.id"))
    public_key  = db.Column(db.String(64), unique=True)
    allowed_ips = db.Column(db.String(256))  # JSON ou CSV
    expires_at  = db.Column(db.DateTime)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
```

---

## Couches de sécurité

```txt
Couche 1 — Authentification Flask
          Rôles, anti-brute-force, sessions (existant)

Couche 2 — WireGuard AllowedIPs côté client
          Le .conf limite ce que l'utilisateur peut router

Couche 3 — WireGuard AllowedIPs côté serveur
          Le peer ne peut joindre que les IPs autorisées

Couche 4 — iptables sur Proxmox
          Filet de sécurité final, indépendant de WireGuard

Couche 5 — Isolation réseau physique
          VMs internes sur adresses ULA, non routables internet
```

---

## Ce qui reste à implémenter

- [ ] Micro-API Flask sur VM WireGuard (add/remove peer)
- [ ] Route `/vpn/request` sur l'Extranet Flask
- [ ] Table `VPNPeer` SQLAlchemy + migration
- [ ] Cron de purge à minuit
- [ ] Règles `iptables` / `ip6tables` sur Proxmox
- [ ] DDNS IPv6 pour stabiliser les endpoints publics
- [ ] QR code optionnel (`qrencode`) pour clients mobiles
