import React from 'react';
import { MathRenderer, useMathProcessor } from './MathRenderer';

interface EnhancedMessageProps {
  content: string;
  className?: string;
}

/**
 * Componente mejorado para mostrar mensajes con fórmulas matemáticas
 */
export const EnhancedMessage: React.FC<EnhancedMessageProps> = ({ 
  content, 
  className = "" 
}) => {
  const { processText } = useMathProcessor();

  // Procesar el contenido para encontrar y renderizar matemáticas
  const processedContent = processText(content);

  return (
    <div className={`enhanced-message ${className}`}>
      {processedContent.map((part, index) => (
        <span key={index}>{part}</span>
      ))}
    </div>
  );
};

/**
 * Función utilitaria para limpiar texto matemático
 */
export const cleanMathText = (text: string): string => {
  return text
    .replace(/\\u202f/g, ' ') // Espacio estrecho sin separación
    .replace(/\\u2062/g, '')  // Función de aplicación invisible
    .replace(/\\u2061/g, '')  // Separador de función invisible
    .replace(/\\u00a0/g, ' ') // Espacio sin separación
    .replace(/\\u2032/g, "'") // Prima
    .replace(/\\u2033/g, "''") // Doble prima
    .replace(/\\\\/g, '\\')   // Doble backslash
    .replace(/\s+/g, ' ')     // Múltiples espacios
    .trim();
};

/**
 * Función para detectar si un texto contiene fórmulas matemáticas
 */
export const containsMath = (text: string): boolean => {
  const mathPatterns = [
    /\$.*?\$/,                    // $formula$
    /\$\$.*?\$\$/,               // $$formula$$
    /\\frac\{.*?\}\{.*?\}/,      // \frac{}{} 
    /\\sqrt\{.*?\}/,             // \sqrt{}
    /\\int.*?dx/,                // Integrales
    /\\sum.*?/,                  // Sumatorias
    /\\lim.*?/,                  // Límites
    /\^[0-9\{\}]/,               // Exponentes
    /_[0-9\{\}]/,                // Subíndices
    /[a-zA-Z]\([a-zA-Z0-9]+\)/,  // Funciones f(x)
  ];
  
  return mathPatterns.some(pattern => pattern.test(text));
};

export default EnhancedMessage;
