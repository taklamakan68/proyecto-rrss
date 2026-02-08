const { exec } = require('child_process');

// Función para ejecutar un archivo
function ejecutar(comando, nombre) {
    return new Promise((resolve) => {
        console.log(`\n▶ Ejecutando: ${nombre}`);
        
        exec(comando, (error, stdout, stderr) => {
            if (error) {
                console.log(`✗ Error en ${nombre}: ${error.message}`);
                resolve(false);
            } else {
                console.log(`✓ ${nombre} completado`);
                if (stdout) console.log(stdout);
                resolve(true);
            }
        });
    });
}

// Ejecutar los 3 archivos en secuencia INFINITAMENTE
async function ejecutarBucleInfinito() {
    let iteracion = 1;
    
    while (true) {
        console.log(`\n${'='.repeat(70)}`);
        console.log(`🔄 ITERACIÓN #${iteracion} - ${new Date().toLocaleString()}`);
        console.log('='.repeat(70));
        
        await ejecutar('python generador_mindfulness.py', 'generador_mindfulness.py');
        await ejecutar('python videolyzer.py', 'videolyzer.py');
        await ejecutar('node instagram.js', 'instagram.js');
        
        console.log(`\n✅ Ciclo ${iteracion} completado`);
        console.log('⏳ Esperando 5 minutos para el próximo ciclo...\n');
        
        // Esperar 5 minutos (300000 ms)
        await new Promise(resolve => setTimeout(resolve, 300000));
        
        iteracion++;
    }
}

console.log('🚀 INICIANDO BOT DE INSTAGRAM 24/7');
console.log('Presiona Ctrl+C para detener\n');

ejecutarBucleInfinito();