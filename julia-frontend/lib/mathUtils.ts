/**
 * Utilidades para limpiar y procesar texto matemático
 */

/**
 * Limpia caracteres Unicode problemáticos en texto matemático
 */
export const cleanMathText = (text: string): string => {
  return text
    // Caracteres Unicode problemáticos
    .replace(/\\u202f/g, ' ')     // Espacio estrecho sin separación
    .replace(/\\u2062/g, '')      // Función de aplicación invisible  
    .replace(/\\u2061/g, '')      // Separador de función invisible
    .replace(/\\u00a0/g, ' ')     // Espacio sin separación
    .replace(/\\u2032/g, "'")     // Prima (')
    .replace(/\\u2033/g, "''")    // Doble prima ('')
    .replace(/\\u2034/g, "'''")   // Triple prima (''')
    .replace(/\\u2070/g, '⁰')     // Superíndice 0
    .replace(/\\u00b9/g, '¹')     // Superíndice 1
    .replace(/\\u00b2/g, '²')     // Superíndice 2
    .replace(/\\u00b3/g, '³')     // Superíndice 3
    .replace(/\\u2074/g, '⁴')     // Superíndice 4
    .replace(/\\u2075/g, '⁵')     // Superíndice 5
    .replace(/\\u2076/g, '⁶')     // Superíndice 6
    .replace(/\\u2077/g, '⁷')     // Superíndice 7
    .replace(/\\u2078/g, '⁸')     // Superíndice 8
    .replace(/\\u2079/g, '⁹')     // Superíndice 9
    
    // Limpiar espacios múltiples
    .replace(/\s+/g, ' ')
    .trim();
};

/**
 * Convierte texto con notación matemática a LaTeX
 */
export const convertToLatex = (text: string): string => {
  return text
    // Limpiar primero
    .replace(/\\u202f/g, ' ')
    .replace(/\\u2062/g, '')
    .replace(/\\u2061/g, '')
    
    // Convertir exponentes simples: x^2 -> x^{2}
    .replace(/\^(\d+)/g, '^{$1}')
    
    // Convertir subíndices: x_1 -> x_{1}
    .replace(/_(\d+)/g, '_{$1}')
    
    // Convertir fracciones: s(t) = 5t^2 -> s(t) = 5t^{2}
    .replace(/(\w+)\((\w+)\)\s*=\s*(\d+)(\w+)\^(\d+)/g, '$1($2) = $3$4^{$5}')
    
    // Añadir espacios alrededor de operadores
    .replace(/([a-zA-Z0-9])\s*=\s*([a-zA-Z0-9])/g, '$1 = $2')
    
    // Limpiar espacios múltiples
    .replace(/\s+/g, ' ')
    .trim();
};

/**
 * Función para procesar texto matemático en mensajes
 */
export const processMathInMessage = (content: string): string => {
  // Si el contenido ya está en LaTeX (contiene $ o $$), no lo proceses
  if (content.includes('$') || content.includes('\\frac') || content.includes('\\sqrt')) {
    return cleanMathText(content);
  }
  
  // Buscar patrones matemáticos comunes y convertirlos
  let processed = cleanMathText(content);
  
  // Convertir expresiones como s(t) = 5t^2 a formato LaTeX
  processed = processed.replace(
    /(\w+)\((\w+)\)\s*=\s*(\d+)(\w+)\^(\d+)/g,
    '$$$1($2) = $3$4^{$5}$$'
  );
  
  // Convertir derivadas s'(t) = 10t
  processed = processed.replace(
    /(\w+)'\((\w+)\)\s*=\s*(\d+)(\w+)/g,
    "$$$1'($2) = $3$4$$"
  );
  
  // Convertir velocidades/unidades: 20 m/s
  processed = processed.replace(
    /(\d+)\s*(m\/s|km\/h|m\/s²|km\/h²)/g,
    '$$\\text{$1 $2}$$'
  );
  
  return processed;
};

export default {
  cleanMathText,
  convertToLatex,
  processMathInMessage
};
