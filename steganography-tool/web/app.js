const PUBLIC_HEADER_MAGIC = "SSG1";
const BUNDLE_HEADER_MAGIC = "BDL1";
const PBKDF2_ITERATIONS = 250000;

const state = {
  encodeMode: "text",
  extractedFile: null,
};

const tabs = [...document.querySelectorAll(".tab")];
const tabPanels = [...document.querySelectorAll(".tab-panel")];

const encodeImageInput = document.getElementById("encode-image");
const filePayloadInput = document.getElementById("file-payload");
const textPayloadInput = document.getElementById("text-payload");
const encodePasswordInput = document.getElementById("encode-password");
const outputNameInput = document.getElementById("output-name");
const encodeSummary = document.getElementById("encode-summary");
const encodeButton = document.getElementById("encode-button");
const encodeReset = document.getElementById("encode-reset");
const encodeProgressFill = document.getElementById("encode-progress-fill");
const encodeProgressText = document.getElementById("encode-progress-text");

const decodeImageInput = document.getElementById("decode-image");
const decodePasswordInput = document.getElementById("decode-password");
const decodeSummary = document.getElementById("decode-summary");
const decodeButton = document.getElementById("decode-button");
const decodeReset = document.getElementById("decode-reset");
const decodeProgressFill = document.getElementById("decode-progress-fill");
const decodeProgressText = document.getElementById("decode-progress-text");
const downloadExtractedButton = document.getElementById("download-extracted");

const textWrap = document.getElementById("text-payload-wrap");
const fileWrap = document.getElementById("file-payload-wrap");
const modeText = document.getElementById("mode-text");
const modeFile = document.getElementById("mode-file");

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((item) => item.classList.toggle("active", item === tab));
    tabPanels.forEach((panel) => panel.classList.toggle("active", panel.id === `${tab.dataset.tab}-tab`));
  });
});

modeText.addEventListener("click", () => setEncodeMode("text"));
modeFile.addEventListener("click", () => setEncodeMode("file"));
encodeButton.addEventListener("click", handleEncode);
decodeButton.addEventListener("click", handleDecode);
encodeReset.addEventListener("click", resetEncode);
decodeReset.addEventListener("click", resetDecode);
downloadExtractedButton.addEventListener("click", downloadExtracted);
encodeImageInput.addEventListener("change", updateCarrierSummary);

function setEncodeMode(mode) {
  state.encodeMode = mode;
  modeText.classList.toggle("active", mode === "text");
  modeFile.classList.toggle("active", mode === "file");
  textWrap.classList.toggle("hidden", mode !== "text");
  fileWrap.classList.toggle("hidden", mode !== "file");
}

function setProgress(target, percent) {
  const safe = Math.max(0, Math.min(100, Math.round(percent)));
  if (target === "encode") {
    encodeProgressFill.style.width = `${safe}%`;
    encodeProgressText.textContent = `${safe}%`;
  } else {
    decodeProgressFill.style.width = `${safe}%`;
    decodeProgressText.textContent = `${safe}%`;
  }
}

function setConsole(target, message) {
  if (target === "encode") {
    encodeSummary.textContent = message;
  } else {
    decodeSummary.textContent = message;
  }
}

function resetEncode() {
  encodeImageInput.value = "";
  filePayloadInput.value = "";
  textPayloadInput.value = "";
  encodePasswordInput.value = "";
  outputNameInput.value = "stego-output.png";
  setEncodeMode("text");
  setProgress("encode", 0);
  setConsole("encode", 'Choose a carrier image, enter the payload, set a password, then click "Save & Encode Image".');
}

function resetDecode() {
  decodeImageInput.value = "";
  decodePasswordInput.value = "";
  state.extractedFile = null;
  downloadExtractedButton.classList.add("hidden");
  setProgress("decode", 0);
  setConsole("decode", "Upload a stego PNG and use the correct password to recover the hidden text or file.");
}

async function updateCarrierSummary() {
  const file = encodeImageInput.files?.[0];
  if (!file) return;
  const image = await loadImage(file);
  const capacity = Math.max((((image.width * image.height * 3) - (57 * 8)) / 8) | 0, 0);
  setConsole(
    "encode",
    `Carrier image loaded
name: ${file.name}
size: ${image.width} x ${image.height}
type: ${file.type || "image"}
approx payload capacity: ${formatBytes(capacity)}`
  );
}

async function handleEncode() {
  try {
    const imageFile = encodeImageInput.files?.[0];
    const password = encodePasswordInput.value;
    if (!imageFile) throw new Error("Choose a carrier image first.");
    if (!password) throw new Error("Enter a password before encoding.");

    setProgress("encode", 10);
    setConsole("encode", "> loading carrier image...");
    const image = await loadImage(imageFile);
    const { canvas, context, imageData } = imageToCanvas(image);

    setProgress("encode", 25);
    const payload = await buildPayloadPackage();
    const bundle = buildBundle(payload);

    setConsole("encode", "> encrypting payload with AES-GCM...");
    const salt = crypto.getRandomValues(new Uint8Array(16));
    const nonce = crypto.getRandomValues(new Uint8Array(12));
    const shuffleSalt = Uint8Array.from(salt).reverse();
    const ciphertext = await encryptData(bundle, password, salt, nonce);

    const publicHeader = buildPublicHeader(salt, shuffleSalt, nonce, ciphertext.length);
    const totalBits = (publicHeader.length + ciphertext.length) * 8;
    const rgbCapacityBits = imageData.data.length / 4 * 3;
    if (totalBits > rgbCapacityBits) {
      throw new Error("Carrier image is too small for this payload.");
    }

    setProgress("encode", 45);
    setConsole("encode", "> generating randomized pixel map...");
    const positions = await getPayloadPositions(imageData.data, password, shuffleSalt, ciphertext.length * 8, publicHeader.length * 8);

    setProgress("encode", 65);
    setConsole("encode", "> embedding encrypted bits...");
    embedBits(imageData.data, 0, bytesToBits(publicHeader));
    embedBitsAtPositions(imageData.data, positions, bytesToBits(ciphertext));
    context.putImageData(imageData, 0, 0);

    setProgress("encode", 85);
    const blob = await canvasToBlob(canvas);
    const fileName = normalizeOutputName(outputNameInput.value);
    triggerDownload(blob, fileName);

    setProgress("encode", 100);
    setConsole(
      "encode",
      `Encoding complete
saved file: ${fileName}
payload type: ${payload.payloadType}
payload size: ${formatBytes(payload.data.length)}
encrypted size: ${formatBytes(ciphertext.length)}
carrier size: ${image.width} x ${image.height}

The PNG download should start automatically.`
    );
  } catch (error) {
    setProgress("encode", 0);
    setConsole("encode", `Encoding failed\n${error.message}`);
  }
}

async function handleDecode() {
  try {
    const imageFile = decodeImageInput.files?.[0];
    const password = decodePasswordInput.value;
    if (!imageFile) throw new Error("Choose a stego PNG image.");
    if (!password) throw new Error("Enter the decode password.");

    setProgress("decode", 12);
    setConsole("decode", "> loading stego image...");
    const image = await loadImage(imageFile);
    const { imageData } = imageToCanvas(image);
    const headerBytes = bitsToBytes(readSequentialBits(imageData.data, 57 * 8));
    const header = parsePublicHeader(headerBytes);

    setProgress("decode", 38);
    setConsole("decode", "> locating randomized payload...");
    const positions = await getPayloadPositions(imageData.data, password, header.shuffleSalt, header.ciphertextLength * 8, 57 * 8);
    const ciphertext = bitsToBytes(readBitsAtPositions(imageData.data, positions));

    setProgress("decode", 68);
    setConsole("decode", "> authenticating and decrypting...");
    const bundle = await decryptData(ciphertext, password, header.salt, header.nonce);
    const payload = parseBundle(bundle);

    setProgress("decode", 100);
    state.extractedFile = payload;
    downloadExtractedButton.classList.remove("hidden");
    setConsole(
      "decode",
      `Decoding complete
type: ${payload.payloadType}
name: ${payload.fileName}
mime: ${payload.mimeType}
size: ${formatBytes(payload.data.length)}

${payload.payloadType === "text" ? payload.textPreview : "Use the download button to save the extracted file."}`
    );
  } catch (error) {
    state.extractedFile = null;
    downloadExtractedButton.classList.add("hidden");
    setProgress("decode", 0);
    setConsole("decode", `Decoding failed\n${error.message}`);
  }
}

async function buildPayloadPackage() {
  if (state.encodeMode === "text") {
    const message = textPayloadInput.value.trim();
    if (!message) throw new Error("Enter a secret message.");
    return {
      payloadType: "text",
      fileName: "message.txt",
      mimeType: "text/plain",
      data: new TextEncoder().encode(message),
    };
  }

  const payloadFile = filePayloadInput.files?.[0];
  if (!payloadFile) throw new Error("Choose a file to hide.");
  return {
    payloadType: "file",
    fileName: payloadFile.name,
    mimeType: payloadFile.type || "application/octet-stream",
    data: new Uint8Array(await payloadFile.arrayBuffer()),
  };
}

function buildBundle(payload) {
  const fileNameBytes = new TextEncoder().encode(payload.fileName);
  const mimeBytes = new TextEncoder().encode(payload.mimeType);
  const header = new Uint8Array(17);
  header.set(new TextEncoder().encode(BUNDLE_HEADER_MAGIC), 0);
  header[4] = payload.payloadType === "text" ? 0 : 1;
  new DataView(header.buffer).setUint16(5, fileNameBytes.length);
  new DataView(header.buffer).setUint16(7, mimeBytes.length);
  new DataView(header.buffer).setBigUint64(9, BigInt(payload.data.length));

  return concatBytes(header, fileNameBytes, mimeBytes, payload.data);
}

function parseBundle(bundle) {
  const view = new DataView(bundle.buffer, bundle.byteOffset, bundle.byteLength);
  const magic = new TextDecoder().decode(bundle.slice(0, 4));
  if (magic !== BUNDLE_HEADER_MAGIC) throw new Error("Invalid hidden payload header.");
  const payloadTypeByte = view.getUint8(4);
  const nameLen = view.getUint16(5);
  const mimeLen = view.getUint16(7);
  const dataLen = Number(view.getBigUint64(9));
  let offset = 17;
  const fileName = new TextDecoder().decode(bundle.slice(offset, offset + nameLen));
  offset += nameLen;
  const mimeType = new TextDecoder().decode(bundle.slice(offset, offset + mimeLen));
  offset += mimeLen;
  const data = bundle.slice(offset, offset + dataLen);

  return {
    payloadType: payloadTypeByte === 0 ? "text" : "file",
    fileName,
    mimeType,
    data,
    textPreview: payloadTypeByte === 0 ? new TextDecoder().decode(data).slice(0, 400) : "",
  };
}

function buildPublicHeader(salt, shuffleSalt, nonce, ciphertextLength) {
  const bytes = new Uint8Array(57);
  bytes.set(new TextEncoder().encode(PUBLIC_HEADER_MAGIC), 0);
  bytes[4] = 1;
  bytes.set(salt, 5);
  bytes.set(shuffleSalt, 21);
  bytes.set(nonce, 37);
  new DataView(bytes.buffer).setBigUint64(49, BigInt(ciphertextLength));
  return bytes;
}

function parsePublicHeader(bytes) {
  const magic = new TextDecoder().decode(bytes.slice(0, 4));
  const version = bytes[4];
  if (magic !== PUBLIC_HEADER_MAGIC || version !== 1) {
    throw new Error("No valid Secure Steganography payload found.");
  }
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  return {
    salt: bytes.slice(5, 21),
    shuffleSalt: bytes.slice(21, 37),
    nonce: bytes.slice(37, 49),
    ciphertextLength: Number(view.getBigUint64(49)),
  };
}

async function encryptData(plainBytes, password, salt, nonce) {
  const key = await deriveAesKey(password, salt, ["encrypt"]);
  const encrypted = await crypto.subtle.encrypt({ name: "AES-GCM", iv: nonce }, key, plainBytes);
  return new Uint8Array(encrypted);
}

async function decryptData(cipherBytes, password, salt, nonce) {
  try {
    const key = await deriveAesKey(password, salt, ["decrypt"]);
    const decrypted = await crypto.subtle.decrypt({ name: "AES-GCM", iv: nonce }, key, cipherBytes);
    return new Uint8Array(decrypted);
  } catch {
    throw new Error("Password is incorrect or the hidden data was modified.");
  }
}

async function deriveAesKey(password, salt, usages) {
  const keyMaterial = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(password),
    "PBKDF2",
    false,
    ["deriveKey"]
  );
  return crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt,
      iterations: PBKDF2_ITERATIONS,
      hash: "SHA-256",
    },
    keyMaterial,
    {
      name: "AES-GCM",
      length: 256,
    },
    false,
    usages
  );
}

async function deriveShuffleSeed(password, shuffleSalt) {
  const keyMaterial = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(password),
    "PBKDF2",
    false,
    ["deriveBits"]
  );
  const bits = await crypto.subtle.deriveBits(
    {
      name: "PBKDF2",
      salt: shuffleSalt,
      iterations: PBKDF2_ITERATIONS,
      hash: "SHA-256",
    },
    keyMaterial,
    64
  );
  const seedBytes = new Uint8Array(bits);
  let seed = 0;
  for (const byte of seedBytes) {
    seed = (seed * 1664525 + byte + 1013904223) >>> 0;
  }
  return seed >>> 0;
}

async function getPayloadPositions(pixelBytes, password, shuffleSalt, bitLength, reservedBits) {
  const candidates = buildCandidateChannels(pixelBytes).filter((position) => position >= reservedBits);
  if (candidates.length < bitLength) {
    throw new Error("Carrier image capacity is insufficient.");
  }
  const seed = await deriveShuffleSeed(password, shuffleSalt);
  shuffleArray(candidates, seed);
  return candidates.slice(0, bitLength);
}

function buildCandidateChannels(pixelBytes) {
  const pixelCount = pixelBytes.length / 4;
  const scores = new Float32Array(pixelCount);

  for (let index = 0; index < pixelCount; index += 1) {
    const base = index * 4;
    const xNextBase = ((index + 1) % pixelCount) * 4;
    const yNextBase = ((index + 64) % pixelCount) * 4;
    const gray = toGray(pixelBytes[base] & 0xfe, pixelBytes[base + 1] & 0xfe, pixelBytes[base + 2] & 0xfe);
    const grayX = toGray(pixelBytes[xNextBase] & 0xfe, pixelBytes[xNextBase + 1] & 0xfe, pixelBytes[xNextBase + 2] & 0xfe);
    const grayY = toGray(pixelBytes[yNextBase] & 0xfe, pixelBytes[yNextBase + 1] & 0xfe, pixelBytes[yNextBase + 2] & 0xfe);
    scores[index] = Math.abs(gray - grayX) + Math.abs(gray - grayY);
  }

  const order = [...Array(pixelCount).keys()].sort((a, b) => scores[b] - scores[a]);
  const ranked = [];
  for (const pixelIndex of order) {
    ranked.push(pixelIndex * 3, pixelIndex * 3 + 1, pixelIndex * 3 + 2);
  }
  return ranked;
}

function toGray(r, g, b) {
  return 0.299 * r + 0.587 * g + 0.114 * b;
}

function embedBits(pixelBytes, bitOffset, bits) {
  for (let i = 0; i < bits.length; i += 1) {
    const rgbIndex = rgbPositionToRgbaOffset(bitOffset + i);
    pixelBytes[rgbIndex] = (pixelBytes[rgbIndex] & 0xfe) | bits[i];
  }
}

function embedBitsAtPositions(pixelBytes, positions, bits) {
  for (let i = 0; i < bits.length; i += 1) {
    const rgbaOffset = rgbPositionToRgbaOffset(positions[i]);
    pixelBytes[rgbaOffset] = (pixelBytes[rgbaOffset] & 0xfe) | bits[i];
  }
}

function readSequentialBits(pixelBytes, count) {
  const bits = new Uint8Array(count);
  for (let i = 0; i < count; i += 1) {
    const rgbaOffset = rgbPositionToRgbaOffset(i);
    bits[i] = pixelBytes[rgbaOffset] & 1;
  }
  return bits;
}

function readBitsAtPositions(pixelBytes, positions) {
  const bits = new Uint8Array(positions.length);
  for (let i = 0; i < positions.length; i += 1) {
    bits[i] = pixelBytes[rgbPositionToRgbaOffset(positions[i])] & 1;
  }
  return bits;
}

function rgbPositionToRgbaOffset(rgbPosition) {
  const pixelIndex = Math.floor(rgbPosition / 3);
  const channel = rgbPosition % 3;
  return pixelIndex * 4 + channel;
}

function bytesToBits(bytes) {
  const bits = new Uint8Array(bytes.length * 8);
  for (let i = 0; i < bytes.length; i += 1) {
    for (let bit = 0; bit < 8; bit += 1) {
      bits[i * 8 + bit] = (bytes[i] >> (7 - bit)) & 1;
    }
  }
  return bits;
}

function bitsToBytes(bits) {
  const bytes = new Uint8Array(Math.ceil(bits.length / 8));
  for (let i = 0; i < bits.length; i += 1) {
    bytes[Math.floor(i / 8)] |= bits[i] << (7 - (i % 8));
  }
  return bytes;
}

function shuffleArray(array, seed) {
  let currentSeed = seed >>> 0;
  const random = () => {
    currentSeed = (1664525 * currentSeed + 1013904223) >>> 0;
    return currentSeed / 4294967296;
  };

  for (let i = array.length - 1; i > 0; i -= 1) {
    const j = Math.floor(random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
}

function concatBytes(...arrays) {
  const totalLength = arrays.reduce((sum, item) => sum + item.length, 0);
  const merged = new Uint8Array(totalLength);
  let offset = 0;
  arrays.forEach((item) => {
    merged.set(item, offset);
    offset += item.length;
  });
  return merged;
}

function normalizeOutputName(name) {
  const base = (name || "stego-output.png").trim() || "stego-output.png";
  return base.toLowerCase().endsWith(".png") ? base : `${base}.png`;
}

function triggerDownload(blob, fileName) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function downloadExtracted() {
  if (!state.extractedFile) return;
  const blob = new Blob([state.extractedFile.data], { type: state.extractedFile.mimeType || "application/octet-stream" });
  triggerDownload(blob, state.extractedFile.fileName || "extracted.bin");
}

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      URL.revokeObjectURL(url);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Unable to read the selected image."));
    };
    image.src = url;
  });
}

function imageToCanvas(image) {
  const canvas = document.createElement("canvas");
  canvas.width = image.width;
  canvas.height = image.height;
  const context = canvas.getContext("2d", { willReadFrequently: true });
  context.drawImage(image, 0, 0);
  const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
  return { canvas, context, imageData };
}

function canvasToBlob(canvas) {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) {
        reject(new Error("Could not generate PNG output."));
        return;
      }
      resolve(blob);
    }, "image/png");
  });
}

function formatBytes(bytes) {
  const units = ["B", "KB", "MB", "GB"];
  let size = Number(bytes);
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`;
}
