const { exec } = require('child_process');

// Rutas de los archivos
const archivos = [
    'C:\\Users\\carlo\\Desktop\\Agni\\generador_mindfulness.py',
    'C:\\Users\\carlo\\Desktop\\Agni\\videolyzer.py',
    'C:\\Users\\carlo\\Desktop\\Agni\\instagram.js'
];

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

// Ejecutar los 3 archivos en secuencia
async function ejecutarTodo() {
    console.log('=== INICIANDO EJECUCIÓN ===\n');
    
    await ejecutar(`python "${archivos[0]}"`, 'generador_mindfulness.py');
    await ejecutar(`python "${archivos[1]}"`, 'videolyzer.py');
    await ejecutar(`node "${archivos[2]}"`, 'instagram.js');
    
    console.log('\n=== PROCESO COMPLETADO ===');
}

ejecutarTodo();