/**
 * AES-GCM 解密函数
 * @param {string} password - 用户输入的密码
 * @param {string} base64Data - Base64 编码的加密数据
 * @returns {Promise<string>} - 解密后的内容
 */
async function decryptAESGCM(password, base64Data) {
  const raw = Uint8Array.from(atob(base64Data), (c) => c.charCodeAt(0));

  const salt = raw.slice(0, 16);
  const iv = raw.slice(16, 28);
  const tag = raw.slice(28, 44);
  const ciphertext = raw.slice(44);

  // 从密码派生 key
  const keyMaterial = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(password),
    "PBKDF2",
    false,
    ["deriveKey"]
  );

  const key = await crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: salt,
      iterations: 100000,
      hash: "SHA-256",
    },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false,
    ["decrypt"]
  );

  // AES-GCM 需要 tag 拼在 ciphertext 后面
  const ciphertextWithTag = new Uint8Array(ciphertext.length + tag.length);
  ciphertextWithTag.set(ciphertext);
  ciphertextWithTag.set(tag, ciphertext.length);

  const decrypted = await crypto.subtle.decrypt(
    {
      name: "AES-GCM",
      iv: iv,
    },
    key,
    ciphertextWithTag
  );

  return new TextDecoder().decode(decrypted);
}

/**
 * 处理密码输入和解密
 */
async function handleDecryption(providedPassword = null) {
  const contentEl = document.getElementById("mdf-encrypt-content");
  const passwordInput = document.getElementById("mdf-password-input");
  const errorMsg = document.getElementById("mdf-error-message");
  const decryptBtn = document.getElementById("mdf-decrypt-btn");
  const modal = document.getElementById("mdf-encrypt-modal");

  if (!contentEl) {
    return;
  }

  const encrypted = contentEl.dataset.encrypted;
  const level = contentEl.dataset.level || "page";
  const path = contentEl.dataset.path || "";

  // 如果没有提供密码，从输入框获取
  let password = providedPassword;
  if (!password && passwordInput) {
    password = passwordInput.value.trim();
  }

  if (!password) {
    if (errorMsg) {
      errorMsg.textContent = "Please enter your password";
      errorMsg.classList.remove("mdf-error-hidden");
    }
    return;
  }

  // 禁用按钮，显示加载状态（如果是手动输入）
  if (!providedPassword && decryptBtn) {
    decryptBtn.disabled = true;
    decryptBtn.textContent = "Decryption in progress...";
  }
  if (errorMsg) {
    errorMsg.classList.add("mdf-error-hidden");
  }

  try {
    const content = await decryptAESGCM(password, encrypted);

    // 解密成功，显示内容并关闭 modal
    contentEl.innerHTML = content;
    contentEl.removeAttribute("data-encrypted");
    contentEl.removeAttribute("data-level");
    contentEl.removeAttribute("data-path");

    if (modal) {
      modal.style.display = "none";
    }

    // 保存密码到 sessionStorage 以便下次访问时自动解密
    if (path) {
      sessionStorage.setItem(`mdf-password-${path}`, password);
    }

    return true;
  } catch (e) {
    console.error("解密失败:", e);

    // 如果是自动尝试解密（使用缓存密码），静默失败
    if (providedPassword) {
      return false;
    }

    // 如果是用户手动输入，显示错误
    if (errorMsg) {
      errorMsg.textContent = "Incorrect password, please try again.";
      errorMsg.classList.remove("mdf-error-hidden");
    }
    if (passwordInput) {
      passwordInput.value = "";
      passwordInput.focus();
    }
    return false;
  } finally {
    if (!providedPassword && decryptBtn) {
      decryptBtn.disabled = false;
      decryptBtn.textContent = "Unlock";
    }
  }
}

/**
 * 尝试使用缓存的密码自动解密
 */
async function tryAutoDecrypt() {
  const contentEl = document.getElementById("mdf-encrypt-content");
  if (!contentEl) return false;

  const level = contentEl.dataset.level || "page";
  const path = contentEl.dataset.path || "";

  // 所有级别都尝试自动解密（如果有缓存密码）
  if (!path) {
    return false;
  }

  // 查找缓存的密码
  const cachedPassword = sessionStorage.getItem(`mdf-password-${path}`);
  if (!cachedPassword) {
    return false;
  }

  // 尝试使用缓存密码解密
  const success = await handleDecryption(cachedPassword);

  if (!success) {
    sessionStorage.removeItem(`mdf-password-${path}`);
  }

  return success;
}

/**
 * 初始化加密内容处理
 */
async function initEncryptedContent() {
  const contentEl = document.getElementById("mdf-encrypt-content");
  if (!contentEl) return;

  const modal = document.getElementById("mdf-encrypt-modal");
  const decryptBtn = document.getElementById("mdf-decrypt-btn");
  const passwordInput = document.getElementById("mdf-password-input");

  // 尝试自动解密（所有级别：page、parent、site）
  const autoDecrypted = await tryAutoDecrypt();

  // 如果自动解密成功，不需要显示 modal
  if (autoDecrypted) {
    if (modal) {
      modal.style.display = "none";
    }
    return;
  }

  // 如果是 page 级别或者没有缓存密码，显示 modal
  if (modal) {
    modal.style.display = "flex";
  }

  // 点击按钮解密
  if (decryptBtn) {
    decryptBtn.addEventListener("click", () => handleDecryption());
  }

  // 按回车键解密
  if (passwordInput) {
    passwordInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        handleDecryption();
      }
    });
  }

  // 防止点击 modal 背景关闭（因为必须解密才能查看）
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        // 可以选择禁止关闭，或者允许用户离开
        // e.preventDefault();
      }
    });
  }
}

// 页面加载完成后初始化
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initEncryptedContent);
} else {
  initEncryptedContent();
}
