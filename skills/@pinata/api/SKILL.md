---
name: pinata-api
description: Pinata IPFS API for file storage, groups, gateways, signatures, x402 payments, and AI-powered vector search.
homepage: https://pinata.cloud
metadata: {"openclaw": {"emoji": "📌", "requires": {"env": ["PINATA_JWT", "PINATA_GATEWAY_URL"]}, "primaryEnv": "PINATA_JWT"}}
---

# pinata-api

Pinata IPFS API skill for file storage, groups, gateways, and more.

## Capabilities

### Files
- Upload files to public or private IPFS networks
- Search, get, update, and delete files
- Filter by name, CID, or MIME type

### Groups
- Create and manage file groups
- Add or remove files from groups

### Gateway & Downloads
- Generate private download links with expiration
- Create signed upload URLs with optional size/type restrictions

### Signatures
- Add, retrieve, and delete cryptographic signatures on files

### Pin By CID
- Pin existing IPFS CIDs to your Pinata account
- Query and cancel pin requests

### x402 Payments
- Create payment instructions for content monetization (USDC on Base)
- Attach CIDs to payment instructions
- List and manage payment instructions

### Vectorize
- Vectorize files for semantic search
- Query vectors by group with natural language
- Delete file vectors

## Environment Variables

- `PINATA_JWT` - Pinata API JWT token for authentication
- `PINATA_GATEWAY_URL` - Your dedicated Pinata gateway URL
