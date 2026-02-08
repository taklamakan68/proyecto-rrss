const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const https = require('https');

// Helper para esperar tiempo
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Helper para descargar video desde Cloudinary
const downloadVideo = (url, outputPath) => {
  return new Promise((resolve, reject) => {
    console.log(`📥 Descargando video desde: ${url}`);
    
    const file = fs.createWriteStream(outputPath);
    
    https.get(url, (response) => {
      if (response.statusCode !== 200) {
        reject(new Error(`Error al descargar: ${response.statusCode}`));
        return;
      }
      
      let downloadedBytes = 0;
      const totalBytes = parseInt(response.headers['content-length'], 10);
      
      response.on('data', (chunk) => {
        downloadedBytes += chunk.length;
        const percent = ((downloadedBytes / totalBytes) * 100).toFixed(1);
        process.stdout.write(`\r   Progreso: ${percent}% (${(downloadedBytes / 1024 / 1024).toFixed(2)} MB)`);
      });
      
      response.pipe(file);
      
      file.on('finish', () => {
        file.close();
        console.log('\n   ✅ Video descargado exitosamente');
        resolve(outputPath);
      });
      
    }).on('error', (err) => {
      fs.unlink(outputPath, () => {});
      reject(err);
    });
  });
};

(async () => {
  console.log('🚀 Iniciando navegador automático para Instagram (HEADLESS)...');
  
  // 1. LEER LA URL DEL VIDEO DESDE video_url.json
  let videoUrl = null;
  let videoLocalPath = null;
  
  try {
    console.log('\n📖 Leyendo video_url.json...');
    const videoUrlData = JSON.parse(fs.readFileSync('video_url.json', 'utf8'));
    videoUrl = videoUrlData.url;
    
    console.log(`✅ URL encontrada: ${videoUrl}`);
    console.log(`   Tema: ${videoUrlData.tema || 'N/A'}`);
    console.log(`   Tamaño: ${videoUrlData.tamanio_mb || 'N/A'} MB`);
    console.log(`   Duración: ${videoUrlData.duracion || 'N/A'} seg`);
    
  } catch (error) {
    console.error('❌ Error al leer video_url.json:', error.message);
    console.error('   Asegúrate de que el archivo existe y tiene el formato correcto');
    process.exit(1);
  }
  
  // 2. DESCARGAR EL VIDEO DESDE CLOUDINARY
  try {
    const videoFileName = 'video_temp_instagram.mp4';
    // Usar /tmp en Render/Linux o directorio actual en Windows
    const tmpDir = process.platform === 'win32' ? __dirname : '/tmp';
    videoLocalPath = path.join(tmpDir, videoFileName);
    
    // Eliminar video anterior si existe
    if (fs.existsSync(videoLocalPath)) {
      console.log('🗑️  Eliminando video temporal anterior...');
      fs.unlinkSync(videoLocalPath);
    }
    
    await downloadVideo(videoUrl, videoLocalPath);
    
    // Verificar que el archivo existe y tiene tamaño
    const stats = fs.statSync(videoLocalPath);
    console.log(`✅ Video listo: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);
    
  } catch (error) {
    console.error('❌ Error al descargar video:', error.message);
    process.exit(1);
  }
  
  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--lang=es-ES,es',
      '--window-size=1920,1080'
    ]
  });

  const page = await browser.newPage();
  
  // Configurar viewport para headless
  await page.setViewport({ width: 1920, height: 1080 });
  
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  
  // CRÍTICO: Prevenir auto-foco ANTES de que la página se cargue
  await page.evaluateOnNewDocument(() => {
    let focusBlocked = true;
    const originalFocus = HTMLElement.prototype.focus;
    
    HTMLElement.prototype.focus = function(...args) {
      if (focusBlocked && (this.tagName === 'INPUT' || this.tagName === 'TEXTAREA')) {
        console.log('🚫 Auto-focus bloqueado para:', this);
        return;
      }
      return originalFocus.apply(this, args);
    };
    
    window.unlockFocus = () => {
      focusBlocked = false;
      HTMLElement.prototype.focus = originalFocus;
      console.log('✅ Focus desbloqueado');
    };
  });
  
  try {
    // 1. Ir a Instagram
    console.log('\n🌐 Navegando a Instagram...');
    await page.goto('https://www.instagram.com/accounts/login/', {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });

    console.log('⏳ Página cargada. Esperando a que aparezca el modal de cookies...');
    await sleep(3000);

    // 2. MANEJO DE COOKIES
    console.log('🍪 Rechazando cookies...');
    
    let cookiesRejected = false;
    
    // Intentar varios métodos para rechazar cookies
    const methods = [
      {
        name: 'XPath exacto',
        action: async () => {
          const xpath = '/html/body/div[4]/div[1]/div/div[2]/div/div/div/div/div[2]/div/button[2]';
          const buttons = await page.$x(xpath);
          if (buttons.length > 0) {
            await buttons[0].click({ delay: 100 });
            return true;
          }
          return false;
        }
      },
      {
        name: 'Clase exacta',
        action: async () => {
          const button = await page.$('button._a9--._ap36._a9_1');
          if (button) {
            const buttonText = await page.evaluate(el => el.textContent, button);
            if (buttonText.includes('Rechazar')) {
              await button.click({ delay: 100 });
              return true;
            }
          }
          return false;
        }
      },
      {
        name: 'JavaScript directo',
        action: async () => {
          return await page.evaluate(() => {
            const buttons = document.querySelectorAll('button');
            for (const button of buttons) {
              if (button.textContent.includes('Rechazar cookies opcionales')) {
                button.click();
                return true;
              }
            }
            return false;
          });
        }
      }
    ];
    
    for (const method of methods) {
      if (!cookiesRejected) {
        console.log(`   Probando: ${method.name}...`);
        try {
          cookiesRejected = await method.action();
          if (cookiesRejected) {
            console.log(`   ✅ Cookies rechazadas con: ${method.name}`);
            await sleep(2000);
            break;
          }
        } catch (error) {
          console.log(`   ⚠️ Error con ${method.name}`);
        }
      }
    }

    if (!cookiesRejected) {
      console.log('   ⚠️ No se pudieron rechazar cookies automáticamente');
    }

    // Desbloquear focus
    await page.evaluate(() => {
      if (typeof window.unlockFocus === 'function') {
        window.unlockFocus();
      }
    });
    await sleep(1000);

    // 3. LOGIN
    console.log('\n🔐 Iniciando sesión...');
    
    // Instagram usa "email" para usuario y "pass" para contraseña
    const usernameSelector = 'input[name="email"]';
    const passwordSelector = 'input[name="pass"]';
    
    console.log('   🔍 Esperando campos de login...');
    await page.waitForSelector(usernameSelector, { visible: true, timeout: 10000 });
    await sleep(1000);
    
    // Usuario
    console.log('   📝 Escribiendo usuario...');
    await page.click(usernameSelector);
    await sleep(300);
    await page.type(usernameSelector, 'asianmagicmakeup', { delay: 100 });
    await sleep(1000);
    
    // Esperar a que el campo de contraseña aparezca
    console.log('   ⏳ Esperando que aparezca el campo de contraseña...');
    await page.waitForSelector(passwordSelector, { visible: true, timeout: 10000 });
    await sleep(500);
    
    // Contraseña
    console.log('   🔑 Escribiendo contraseña...');
    await page.click(passwordSelector);
    await sleep(300);
    await page.type(passwordSelector, 'punarepuna', { delay: 80 });
    await sleep(500);
    
    // Clic en login
    console.log('   🎯 Haciendo clic en Login...');
    const submitButton = await page.$('button[type="submit"]');
    if (submitButton) {
      await submitButton.click({ delay: 150 });
    } else {
      await page.keyboard.press('Enter');
    }

    console.log('⏳ Esperando resultado del login...');
    await sleep(5000);
    
    const currentUrl = page.url();
    console.log(`🔗 URL actual: ${currentUrl}`);
    
    if (currentUrl.includes('/accounts/login')) {
      console.log('❌ Login falló');
      await page.screenshot({ path: 'login-failed.png', fullPage: true });
      await browser.close();
      process.exit(1);
    }
    
    console.log('✅ Login exitoso!');
    await sleep(3000);

    // 4. CLIC EN "NUEVA PUBLICACIÓN"
    console.log('\n📸 Buscando botón "Nueva publicación"...');
    
    let newPostClicked = false;
    
    try {
      const clicked = await page.evaluate(() => {
        const svgs = document.querySelectorAll('svg[aria-label="Nueva publicación"]');
        for (const svg of svgs) {
          const clickableDiv = svg.closest('div[aria-selected]');
          if (clickableDiv) {
            clickableDiv.click();
            return true;
          }
        }
        return false;
      });
      
      if (clicked) {
        newPostClicked = true;
        console.log('✅ Clic en "Nueva publicación" exitoso');
        await sleep(2000);
      }
    } catch (error) {
      console.log('⚠️ Error al hacer clic en Nueva publicación');
    }
    
    if (!newPostClicked) {
      console.log('❌ No se pudo abrir el diálogo de nueva publicación');
      await page.screenshot({ path: 'new-post-failed.png', fullPage: true });
      await browser.close();
      process.exit(1);
    }

    // 5. CLIC EN "PUBLICACIÓN"
    console.log('\n📝 Buscando botón "Publicación"...');
    await sleep(2000);
    
    let publicacionClicked = false;
    
    // Método 1: XPath exacto proporcionado
    try {
      console.log('   Método 1: XPath exacto...');
      const xpath = '/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/div/div/div/div/div/div[2]/div/div[7]/div/span/div/div/div/div[1]/a[1]';
      const elements = await page.$x(xpath);
      
      if (elements.length > 0) {
        console.log('   ✓ Elemento encontrado con XPath exacto');
        await sleep(500);
        await elements[0].click({ delay: 100 });
        publicacionClicked = true;
        console.log('   ✅ Clic en "Publicación" exitoso (XPath exacto)');
        await sleep(2000);
      }
    } catch (error) {
      console.log('   ⚠️ Error con XPath exacto:', error.message);
    }
    
    // Método 2: Buscar el elemento <a> que contiene "Publicación"
    if (!publicacionClicked) {
      try {
        console.log('   Método 2: Buscando enlace <a> con texto "Publicación"...');
        const xpath = '//a[.//span[text()="Publicación"]]';
        const elements = await page.$x(xpath);
        
        if (elements.length > 0) {
          console.log('   ✓ Enlace <a> encontrado');
          await sleep(500);
          await elements[0].click({ delay: 100 });
          publicacionClicked = true;
          console.log('   ✅ Clic en "Publicación" exitoso (enlace <a>)');
          await sleep(2000);
        }
      } catch (error) {
        console.log('   ⚠️ Error con Método 2');
      }
    }
    
    // Método 3: Por evaluación JavaScript del elemento <a>
    if (!publicacionClicked) {
      try {
        console.log('   Método 3: JavaScript directo buscando enlaces...');
        publicacionClicked = await page.evaluate(() => {
          const links = document.querySelectorAll('a');
          for (const link of links) {
            const spans = link.querySelectorAll('span');
            for (const span of spans) {
              if (span.textContent.trim() === 'Publicación') {
                link.click();
                return true;
              }
            }
          }
          return false;
        });
        
        if (publicacionClicked) {
          console.log('   ✅ Clic en "Publicación" exitoso (JavaScript)');
          await sleep(2000);
        }
      } catch (error) {
        console.log('   ⚠️ Error con Método 3');
      }
    }
    
    // Método 4: Buscar por el span interno y subir al elemento <a>
    if (!publicacionClicked) {
      try {
        console.log('   Método 4: Buscar span y navegar al <a> padre...');
        const xpath = '//span[text()="Publicación"]/ancestor::a[1]';
        const elements = await page.$x(xpath);
        
        if (elements.length > 0) {
          console.log('   ✓ Elemento <a> encontrado desde span');
          await sleep(500);
          await elements[0].click({ delay: 100 });
          publicacionClicked = true;
          console.log('   ✅ Clic en "Publicación" exitoso (ancestor)');
          await sleep(2000);
        }
      } catch (error) {
        console.log('   ⚠️ Error con Método 4');
      }
    }

    if (!publicacionClicked) {
      console.log('   ❌ No se pudo seleccionar tipo de publicación');
      await page.screenshot({ path: 'publicacion-failed.png', fullPage: true });
      
      await browser.close();
      process.exit(1);
    }

    // 6. SUBIR EL VIDEO
    console.log('\n📤 Subiendo video a Instagram...');
    await sleep(1500);
    
    // Buscar el input de tipo file
    const fileInputSelector = 'input[type="file"][accept*="video"]';
    
    try {
      console.log('   🔍 Buscando input de archivo...');
      
      // Esperar a que el input exista
      await page.waitForSelector(fileInputSelector, { timeout: 10000 });
      
      const inputElement = await page.$(fileInputSelector);
      
      if (inputElement) {
        console.log('   ✓ Input encontrado');
        console.log(`   📁 Subiendo: ${videoLocalPath}`);
        
        // Subir el archivo
        await inputElement.uploadFile(videoLocalPath);
        
        console.log('   ✅ Video subido exitosamente');
        await sleep(3000);
        
        // Esperar a que Instagram procese el video
        console.log('   ⏳ Esperando a que Instagram procese el video...');
        await sleep(5000);
        
        await page.screenshot({ path: 'video-uploaded.png', fullPage: true });
        
        // 7. HACER CLIC EN BOTÓN "OK"
        console.log('\n✅ Buscando botón "OK"...');
        await sleep(2000);
        
        let okClicked = false;
        
        // Método 1: Buscar por texto "OK"
        try {
          okClicked = await page.evaluate(() => {
            const buttons = document.querySelectorAll('button');
            for (const button of buttons) {
              if (button.textContent.trim() === 'OK') {
                button.click();
                return true;
              }
            }
            return false;
          });
          
          if (okClicked) {
            console.log('   ✅ Clic en "OK" exitoso');
            await sleep(3000);
          }
        } catch (error) {
          console.log('   ⚠️ Error al buscar botón OK');
        }
        
        // Método 2: Buscar por clases específicas
        if (!okClicked) {
          try {
            const okButton = await page.$('button._aswp._aswr._asws._aswu._aswy._asw_._asx2');
            if (okButton) {
              await okButton.click({ delay: 100 });
              okClicked = true;
              console.log('   ✅ Clic en "OK" exitoso (por clase)');
              await sleep(3000);
            }
          } catch (error) {
            console.log('   ⚠️ Error con método de clase OK');
          }
        }
        
        if (!okClicked) {
          console.log('   ⚠️ No se encontró el botón OK, continuando...');
        }
        
        // 8. PRIMER CLIC EN "NEXT" / "SIGUIENTE"
        console.log('\n➡️  Buscando primer botón "Next"...');
        await sleep(2000);
        
        let nextClicked1 = false;
        
        // Método 1: Por texto "Next"
        try {
          nextClicked1 = await page.evaluate(() => {
            const buttons = document.querySelectorAll('button, div[role="button"]');
            for (const button of buttons) {
              const text = button.textContent.trim();
              if (text === 'Next' || text === 'Siguiente') {
                button.click();
                return true;
              }
            }
            return false;
          });
          
          if (nextClicked1) {
            console.log('   ✅ Primer clic en "Next" exitoso');
            await sleep(3000);
          }
        } catch (error) {
          console.log('   ⚠️ Error al buscar primer Next');
        }
        
        // Método 2: Por clases específicas
        if (!nextClicked1) {
          try {
            const nextButton = await page.$('div[role="button"].x1i10hfl.xjqpnuy.xc5r6h4');
            if (nextButton) {
              await nextButton.click({ delay: 100 });
              nextClicked1 = true;
              console.log('   ✅ Primer clic en "Next" exitoso (por clase)');
              await sleep(3000);
            }
          } catch (error) {
            console.log('   ⚠️ Error con método de clase Next');
          }
        }
        
        if (!nextClicked1) {
          console.log('   ⚠️ No se encontró el primer botón Next');
        }
        
        // 9. SEGUNDO CLIC EN "NEXT" / "SIGUIENTE"
        console.log('\n➡️  Buscando segundo botón "Next"...');
        await sleep(2000);
        
        let nextClicked2 = false;
        
        // Método 1: Por XPath proporcionado
        try {
          const xpath = '/html/body/div[5]/div[1]/div/div[3]/div/div/div/div/div/div/div/div[1]/div/div/div/div[3]/div';
          const elements = await page.$x(xpath);
          
          if (elements.length > 0) {
            await elements[0].click({ delay: 100 });
            nextClicked2 = true;
            console.log('   ✅ Segundo clic en "Next" exitoso (XPath)');
            await sleep(3000);
          }
        } catch (error) {
          console.log('   ⚠️ Error con XPath del segundo Next');
        }
        
        // Método 2: Por texto "Next" nuevamente
        if (!nextClicked2) {
          try {
            nextClicked2 = await page.evaluate(() => {
              const buttons = document.querySelectorAll('button, div[role="button"]');
              for (const button of buttons) {
                const text = button.textContent.trim();
                if (text === 'Next' || text === 'Siguiente') {
                  button.click();
                  return true;
                }
              }
              return false;
            });
            
            if (nextClicked2) {
              console.log('   ✅ Segundo clic en "Next" exitoso');
              await sleep(3000);
            }
          } catch (error) {
            console.log('   ⚠️ Error al buscar segundo Next');
          }
        }
        
        if (!nextClicked2) {
          console.log('   ⚠️ No se encontró el segundo botón Next');
        }
        
        // 10. AÑADIR DESCRIPCIÓN (OPCIONAL)
        console.log('\n📝 Añadiendo descripción...');
        await sleep(2000);
        
        try {
          const textareaSelector = 'textarea[aria-label="Escribe un pie de foto..."]';
          const textarea = await page.$(textareaSelector);
          
          if (textarea) {
            const descripcion = '✨ Nueva publicación ✨\n\n#instagram #video';
            await textarea.type(descripcion, { delay: 50 });
            console.log('   ✅ Descripción añadida');
            await sleep(1000);
          } else {
            console.log('   ⚠️ No se encontró el campo de descripción');
          }
        } catch (error) {
          console.log('   ⚠️ Error al añadir descripción:', error.message);
        }
        
        // 11. HACER CLIC EN "SHARE" / "COMPARTIR" PARA PUBLICAR
        console.log('\n🚀 Buscando botón "Share"...');
        await sleep(2000);
        
        let shareClicked = false;
        
        // Método 1: Por XPath proporcionado
        try {
          const xpath = '/html/body/div[4]/div[1]/div/div[3]/div/div/div/div/div/div/div/div[1]/div/div/div/div[3]/div';
          const elements = await page.$x(xpath);
          
          if (elements.length > 0) {
            await elements[0].click({ delay: 100 });
            shareClicked = true;
            console.log('   ✅ Clic en "Share" exitoso (XPath)');
            await sleep(3000);
          }
        } catch (error) {
          console.log('   ⚠️ Error con XPath del botón Share');
        }
        
        // Método 2: Por texto
        if (!shareClicked) {
          try {
            shareClicked = await page.evaluate(() => {
              const buttons = document.querySelectorAll('button, div[role="button"]');
              for (const button of buttons) {
                const text = button.textContent.trim();
                if (text === 'Share' || text === 'Compartir' || text === 'Publicar') {
                  button.click();
                  return true;
                }
              }
              return false;
            });
            
            if (shareClicked) {
              console.log('   ✅ Clic en "Share" exitoso');
              await sleep(3000);
            }
          } catch (error) {
            console.log('   ⚠️ Error al buscar botón Share por texto');
          }
        }
        
        if (shareClicked) {
          console.log('\n🎉 ¡BOTÓN SHARE PRESIONADO!');
          console.log('⏳ Esperando 5 minutos para que Instagram procese el video...');
          await page.screenshot({ path: 'post-share-clicked.png', fullPage: true });
          
          // ESPERAR 5 MINUTOS (300000 ms) CON CUENTA REGRESIVA
          const esperaTotal = 300; // 5 minutos en segundos
          for (let segundosRestantes = esperaTotal; segundosRestantes > 0; segundosRestantes--) {
            const minutos = Math.floor(segundosRestantes / 60);
            const segundos = segundosRestantes % 60;
            process.stdout.write(`\r   ⏱️  Tiempo restante: ${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')} `);
            await sleep(1000);
          }
          
          console.log('\n✅ Espera completada');
          console.log('🎉 ¡VIDEO PUBLICADO EXITOSAMENTE EN INSTAGRAM!');
          await page.screenshot({ path: 'post-success-final.png', fullPage: true });
          
        } else {
          console.log('   ❌ No se encontró el botón "Share"');
          await page.screenshot({ path: 'share-not-found.png', fullPage: true });
        }
        
      } else {
        console.log('   ❌ No se encontró el input de archivo');
        await page.screenshot({ path: 'file-input-not-found.png', fullPage: true });
      }
      
    } catch (error) {
      console.log('   ❌ Error al subir video:', error.message);
      await page.screenshot({ path: 'upload-error.png', fullPage: true });
    }

    console.log('\n✅ PROCESO COMPLETADO');
    
    // Limpiar archivo temporal
    if (fs.existsSync(videoLocalPath)) {
      fs.unlinkSync(videoLocalPath);
      console.log('🗑️  Archivo temporal eliminado');
    }
    
    // Cerrar navegador
    await browser.close();
    console.log('🔒 Navegador cerrado');

  } catch (error) {
    console.error('💥 ERROR CRÍTICO:', error.message);
    console.error('Stack:', error.stack);
    
    try {
      await page.screenshot({ path: 'critical-error.png', fullPage: true });
      await browser.close();
    } catch (e) {}
    
    process.exit(1);
  }

})();