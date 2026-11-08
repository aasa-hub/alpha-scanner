import { z } from "zod";

const PINATA_JWT = process.env.PINATA_JWT;
const PINATA_GATEWAY_URL = process.env.PINATA_GATEWAY_URL;

const getHeaders = () => {
  if (!PINATA_JWT) {
    throw new Error("PINATA_JWT environment variable is not set");
  }
  return {
    Authorization: `Bearer ${PINATA_JWT}`,
    "Content-Type": "application/json",
  };
};

// Schemas
export const networkSchema = z.enum(["public", "private"]).default("public");
export const blockchainNetworkSchema = z.enum(["base", "base-sepolia"]).default("base");

// USDC addresses
const USDC_ADDRESSES: Record<string, string> = {
  base: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  "base-sepolia": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
};

// =============================================================================
// Authentication
// =============================================================================

export async function testAuthentication() {
  const response = await fetch("https://api.pinata.cloud/data/testAuthentication", {
    method: "GET",
    headers: getHeaders(),
  });
  if (!response.ok) throw new Error(`Authentication failed: ${response.status}`);
  return response.json();
}

// =============================================================================
// Files
// =============================================================================

export async function searchFiles(params: {
  network?: "public" | "private";
  name?: string;
  cid?: string;
  mimeType?: string;
  limit?: number;
  pageToken?: string;
}) {
  const { network = "public", name, cid, mimeType, limit, pageToken } = params;
  const query = new URLSearchParams();
  if (name) query.append("name", name);
  if (cid) query.append("cid", cid);
  if (mimeType) query.append("mimeType", mimeType);
  if (limit) query.append("limit", limit.toString());
  if (pageToken) query.append("pageToken", pageToken);

  const response = await fetch(`https://api.pinata.cloud/v3/files/${network}?${query}`, {
    method: "GET",
    headers: getHeaders(),
  });
  if (!response.ok) throw new Error(`Failed to search files: ${response.status}`);
  return response.json();
}

export async function getFileById(params: { network?: "public" | "private"; id: string }) {
  const { network = "public", id } = params;
  const response = await fetch(`https://api.pinata.cloud/v3/files/${network}/${id}`, {
    method: "GET",
    headers: getHeaders(),
  });
  if (!response.ok) throw new Error(`Failed to get file: ${response.status}`);
  return response.json();
}

export async function updateFile(params: {
  network?: "public" | "private";
  id: string;
  name?: string;
  keyvalues?: Record<string, unknown>;
}) {
  const { network = "public", id, name, keyvalues } = params;
  const payload: { name?: string; keyvalues?: Record<string, unknown> } = {};
  if (name) payload.name = name;
  if (keyvalues) payload.keyvalues = keyvalues;

  const response = await fetch(`https://api.pinata.cloud/v3/files/${network}/${id}`, {
    method: "PUT",
    headers: getHeaders(),
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`Failed to update file: ${response.status}`);
  return response.json();
}

export async function deleteFile(params: { network?: "public" | "private"; id: string }) {
  const { network = "public", id } = params;
  const response = await fetch(`https://api.pinata.cloud/v3/files/${network}/${id}`, {
    method: "DELETE",
    headers: getHeaders(),
  });
  if (!response.ok) throw new Error(`Failed to delete file: ${response.status}`);
  return response.json();
}

export async function uploadFile(params: {
  file: Blob;
  fileName: string;
  network?: "public" | "private";
  group_id?: string;
  keyvalues?: Record<string, string>;
}) {
  const { file, fileName, network = "public", group_id, keyvalues } = params;

  const formData = new FormData();
  formData.append("file", file, fileName);
  formData.append("network", network);
  if (group_id) formData.append("group_id", group_id);
  if (keyvalues) formData.append("keyvalues", JSON.stringify(keyvalues));

  const response = await fetch("https://uploads.pinata.cloud/v3/files", {
    method: "POST",
    headers: { Authorization: `Bearer ${PINATA_JWT}` },
    body: formData,
  });
  if (!response.ok) throw new Error(`Failed to upload file: ${response.status}`);
  return response.json();
}

// =============================================================================
// Groups
// =============================================================================

export async function listGroups(params: {
  network?: "public" | "private";
  name?: string;
  limit?: number;
  pageToken?: string;
}) {
  const { network = "public", name, limit, pageToken } = params;
  const query = new URLSearchParams();
  if (name) query.append("name", name);
  if (limit) query.append("limit", limit.toString());
  if (pageToken) query.append("pageToken", pageToken);

  const response = await fetch(`https://api.pinata.cloud/v3/groups/${network}?${query}`, {
    method: "GET",
    headers: getHeaders(),
  });
  if (!response.ok) throw new Error(`Failed to list groups: ${response.status}`);
  return response.json();
}

export async function createGroup(params: { network?: "public" | "private"; name: string }) {
  const { network = "public", name } = params;
  const response = await fetch(`https://api.pinata.cloud/v3/groups/${network}`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ name }),
  });
  if (!response.ok) throw new Error(`Failed to create group: ${response.status}`);
  return response.json();
}

export async function getGroup(params: { network?: "public" | "private"; id: string }) {
  const { network = "public", id } = params;
  const response = await fetch(`https://api.pinata.cloud/v3/groups/${network}/${id}`, {
    method: "GET",
    headers: getHeaders(),
  });
  if (!response.ok) throw new Error(`Failed to get group: ${response.status}`);
  return response.json();
}

export async function updateGroup(params: {
  network?: "public" | "private";
  id: string;
  name: string;
}) {
  const { network = "public", id, name } = params;
  const response = await fetch(`https://api.pinata.cloud/v3/groups/${network}/${id}`, {
    method: "PUT",
    headers: getHeaders(),
    body: JSON.stringify({ name }),
  });
  if (!response.ok) throw new Error(`Failed to update group: ${response.status}`);
  return response.json();
}

export async function deleteGroup(params: { network?: "public" | "private"; id: string }) {
  const { network = "public", id } = params;
  const response = await fetch(`https://api.pinata.cloud/v3/groups/${network}/${id}`, {
    method: "DELETE",
    headers: getHeaders(),
  });
  if (!response.ok) throw new Error(`Failed to delete group: ${response.status}`);
  return response.json();
}

export async function addFileToGroup(params: {
  network?: "public" | "private";
  groupId: string;
  fileId: string;
}) {
  const { network = "public", groupId, fileId } = params;
  const response = await fetch(
    `https://api.pinata.cloud/v3/groups/${network}/${groupId}/ids/${fileId}`,
    { method: "PUT", headers: getHeaders() }
  );
  if (!response.ok) throw new Error(`Failed to add file to group: ${response.status}`);
  return response.json();
}

export async function removeFileFromGroup(params: {
  network?: "public" | "private";
  groupId: string;
  fileId: string;
}) {
  const { network = "public", groupId, fileId } = params;
  const response = await fetch(
    `https://api.pinata.cloud/v3/groups/${network}/${groupId}/ids/${fileId}`,
    { method: "DELETE", headers: getHeaders() }
  );
  if (!response.ok) throw new Error(`Failed to remove file from group: ${response.status}`);
  return response.json();
}

// =============================================================================
// Gateway & Downloads
// =============================================================================

export async function createPrivateDownloadLink(params: { cid: string; expires?: number }) {
  const { cid, expires = 600 } = params;
  if (!PINATA_GATEWAY_URL) throw new Error("PINATA_GATEWAY_URL environment variable is not set");

  const response = await fetch("https://api.pinata.cloud/v3/files/private/download_link", {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({
      url: `https://${PINATA_GATEWAY_URL}/files/${cid}`,
      expires,
      date: Math.floor(Date.now() / 1000),
      method: "GET",
    }),
  });
  if (!response.ok) throw new Error(`Failed to create download link: ${response.status}`);
  return response.json();
}

export async function createSignedUploadUrl(params: {
  expires: number;
  max_file_size?: number;
  allow_mime_types?: string[];
  group_id?: string;
  filename?: string;
  keyvalues?: Record<string, string>;
}) {
  const { expires, max_file_size, allow_mime_types, group_id, filename, keyvalues } = params;

  const payload: Record<string, unknown> = {
    date: Math.floor(Date.now() / 1000),
    expires,
  };
  if (max_file_size) payload.max_file_size = max_file_size;
  if (allow_mime_types) payload.allow_mime_types = allow_mime_types;
  if (group_id) payload.group_id = group_id;
  if (filename) payload.filename = filename;
  if (keyvalues) payload.keyvalues = keyvalues;

  const response = await fetch("https://uploads.pinata.cloud/v3/files/sign", {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`Failed to create signed upload URL: ${response.status}`);
  return response.json();
}

// =============================================================================
// Signatures
// =============================================================================

export async function addSignature(params: {
  network?: "public" | "private";
  cid: string;
  signature: string;
  address: string;
}) {
  const { network = "public", cid, signature, address } = params;
  const response = await fetch(
    `https://api.pinata.cloud/v3/files/${network}/signature/${cid}`,
    {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ signature, address }),
    }
  );
  if (!response.ok) throw new Error(`Failed to add signature: ${response.status}`);
  return response.json();
}

export async function getSignature(params: { network?: "public" | "private"; cid: string }) {
  const { network = "public", cid } = params;
  const response = await fetch(
    `https://api.pinata.cloud/v3/files/${network}/signature/${cid}`,
    { method: "GET", headers: getHeaders() }
  );
  if (!response.ok) throw new Error(`Failed to get signature: ${response.status}`);
  return response.json();
}

export async function deleteSignature(params: { network?: "public" | "private"; cid: string }) {
  const { network = "public", cid } = params;
  const response = await fetch(
    `https://api.pinata.cloud/v3/files/${network}/signature/${cid}`,
    { method: "DELETE", headers: getHeaders() }
  );
  if (!response.ok) throw new Error(`Failed to delete signature: ${response.status}`);
  return response.json();
}

// =============================================================================
// Pin By CID
// =============================================================================

export async function pinByCid(params: {
  cid: string;
  name?: string;
  group_id?: string;
  keyvalues?: Record<string, string>;
  host_nodes?: string[];
}) {
  const { cid, name, group_id, keyvalues, host_nodes } = params;

  const payload: Record<string, unknown> = { cid };
  if (name) payload.name = name;
  if (group_id) payload.group_id = group_id;
  if (keyvalues) payload.keyvalues = keyvalues;
  if (host_nodes) payload.host_nodes = host_nodes;

  const response = await fetch("https://api.pinata.cloud/v3/files/public/pin_by_cid", {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`Failed to pin CID: ${response.status}`);
  return response.json();
}

export async function queryPinRequests(params: {
  order?: "ASC" | "DESC";
  status?: string;
  cid?: string;
  limit?: number;
  pageToken?: string;
}) {
  const { order, status, cid, limit, pageToken } = params;
  const query = new URLSearchParams();
  if (order) query.append("order", order);
  if (status) query.append("status", status);
  if (cid) query.append("cid", cid);
  if (limit) query.append("limit", limit.toString());
  if (pageToken) query.append("pageToken", pageToken);

  const response = await fetch(
    `https://api.pinata.cloud/v3/files/public/pin_by_cid?${query}`,
    { method: "GET", headers: getHeaders() }
  );
  if (!response.ok) throw new Error(`Failed to query pin requests: ${response.status}`);
  return response.json();
}

export async function cancelPinRequest(params: { id: string }) {
  const response = await fetch(
    `https://api.pinata.cloud/v3/files/public/pin_by_cid/${params.id}`,
    { method: "DELETE", headers: getHeaders() }
  );
  if (!response.ok) throw new Error(`Failed to cancel pin request: ${response.status}`);
  return response.json();
}

// =============================================================================
// x402 Payment Instructions
// =============================================================================

export async function createPaymentInstruction(params: {
  name: string;
  pay_to: string;
  amount_usdc: string;
  network?: "base" | "base-sepolia";
  description?: string;
}) {
  const { name, pay_to, amount_usdc, network = "base", description } = params;
  const amountInSmallestUnit = Math.round(parseFloat(amount_usdc) * 1_000_000).toString();

  const payload: Record<string, unknown> = {
    name,
    payment_requirements: [
      {
        asset: USDC_ADDRESSES[network],
        pay_to,
        network,
        amount: amountInSmallestUnit,
      },
    ],
  };
  if (description) payload.description = description;

  const response = await fetch("https://api.pinata.cloud/v3/x402/payment_instructions", {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`Failed to create payment instruction: ${response.status}`);
  return response.json();
}

export async function listPaymentInstructions(params: {
  limit?: number;
  pageToken?: string;
  cid?: string;
  name?: string;
  id?: string;
}) {
  const { limit, pageToken, cid, name, id } = params;
  const query = new URLSearchParams();
  if (limit) query.append("limit", limit.toString());
  if (pageToken) query.append("pageToken", pageToken);
  if (cid) query.append("cid", cid);
  if (name) query.append("name", name);
  if (id) query.append("id", id);

  const response = await fetch(
    `https://api.pinata.cloud/v3/x402/payment_instructions?${query}`,
    { method: "GET", headers: getHeaders() }
  );
  if (!response.ok) throw new Error(`Failed to list payment instructions: ${response.status}`);
  return response.json();
}

export async function getPaymentInstruction(params: { id: string }) {
  const response = await fetch(
    `https://api.pinata.cloud/v3/x402/payment_instructions/${params.id}`,
    { method: "GET", headers: getHeaders() }
  );
  if (!response.ok) throw new Error(`Failed to get payment instruction: ${response.status}`);
  return response.json();
}

export async function deletePaymentInstruction(params: { id: string }) {
  const response = await fetch(
    `https://api.pinata.cloud/v3/x402/payment_instructions/${params.id}`,
    { method: "DELETE", headers: getHeaders() }
  );
  if (!response.ok) throw new Error(`Failed to delete payment instruction: ${response.status}`);
  return response.json();
}

export async function addCidToPaymentInstruction(params: { id: string; cid: string }) {
  const { id, cid } = params;
  const response = await fetch(
    `https://api.pinata.cloud/v3/x402/payment_instructions/${id}/cids/${cid}`,
    { method: "PUT", headers: getHeaders() }
  );
  if (!response.ok) throw new Error(`Failed to add CID to payment instruction: ${response.status}`);
  return response.json();
}

export async function removeCidFromPaymentInstruction(params: { id: string; cid: string }) {
  const { id, cid } = params;
  const response = await fetch(
    `https://api.pinata.cloud/v3/x402/payment_instructions/${id}/cids/${cid}`,
    { method: "DELETE", headers: getHeaders() }
  );
  if (!response.ok)
    throw new Error(`Failed to remove CID from payment instruction: ${response.status}`);
  return response.json();
}

// =============================================================================
// Vectorize
// =============================================================================

export async function vectorizeFile(params: { file_id: string }) {
  const response = await fetch(
    `https://uploads.pinata.cloud/v3/vectorize/files/${params.file_id}`,
    { method: "POST", headers: getHeaders() }
  );
  if (!response.ok) throw new Error(`Failed to vectorize file: ${response.status}`);
  return response.json();
}

export async function deleteFileVectors(params: { file_id: string }) {
  const response = await fetch(
    `https://uploads.pinata.cloud/v3/vectorize/files/${params.file_id}`,
    { method: "DELETE", headers: getHeaders() }
  );
  if (!response.ok) throw new Error(`Failed to delete file vectors: ${response.status}`);
  return response.json();
}

export async function queryVectors(params: { group_id: string; text: string }) {
  const { group_id, text } = params;
  const response = await fetch(
    `https://uploads.pinata.cloud/v3/vectorize/groups/${group_id}/query`,
    {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ text }),
    }
  );
  if (!response.ok) throw new Error(`Failed to query vectors: ${response.status}`);
  return response.json();
}
