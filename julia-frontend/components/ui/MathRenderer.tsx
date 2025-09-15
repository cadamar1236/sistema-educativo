import React from 'react';
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';

interface MathRendererProps {
  children: string;
  block?: boolean;
}

/**
 * Componente para renderizar fórmulas matemáticas usando KaTeX
 */
export const MathRenderer: React.FC<MathRendererProps> = ({ children, block = false }) => {
  // Limpiar caracteres Unicode problemáticos
  const cleanMath = children
    .replace(/\\u202f/g, ' ') // Espacio estrecho sin separación
    .replace(/\\u2062/g, '')  // Función de aplicación invisible
    .replace(/\\u2061/g, '')  // Separador de función invisible
    .replace(/\\u00a0/g, ' ') // Espacio sin separación
    .replace(/\\u2032/g, "'") // Prima
    .replace(/\\u2033/g, "''") // Doble prima
    .trim();

  try {
    if (block) {
      return <BlockMath math={cleanMath} />;
    } else {
      return <InlineMath math={cleanMath} />;
    }
  } catch (error) {
    console.warn('Error renderizando matemáticas:', error);
    // Fallback: mostrar el texto sin procesar
    return <code className="math-fallback">{children}</code>;
  }
};

/**
 * Hook para procesar texto con fórmulas matemáticas
 */
export const useMathProcessor = () => {
  const processText = (text: string): React.ReactNode[] => {
    const parts: React.ReactNode[] = [];
    
    // Expresiones regulares para diferentes tipos de matemáticas
    const inlineMathRegex = /\$([^$]+)\$/g; // $formula$
    const blockMathRegex = /\$\$([^$]+)\$\$/g; // $$formula$$
    const latexRegex = /\\\\begin\{.*?\}.*?\\\\end\{.*?\}/gs; // LaTeX blocks
    
    let lastIndex = 0;
    let match;
    
    // Procesar bloques de matemáticas $$...$$
    const blockMatches = [...text.matchAll(blockMathRegex)];
    blockMatches.forEach((match, index) => {
      const before = text.slice(lastIndex, match.index);
      if (before) {
        parts.push(before);
      }
      
      parts.push(
        <MathRenderer key={`block-${index}`} block={true}>
          {match[1]}
        </MathRenderer>
      );
      
      lastIndex = match.index! + match[0].length;
    });
    
    // Procesar matemáticas inline $...$
    const remainingText = text.slice(lastIndex);
    const inlineMatches = [...remainingText.matchAll(inlineMathRegex)];
    
    let inlineLastIndex = 0;
    inlineMatches.forEach((match, index) => {
      const before = remainingText.slice(inlineLastIndex, match.index);
      if (before) {
        parts.push(before);
      }
      
      parts.push(
        <MathRenderer key={`inline-${index}`} block={false}>
          {match[1]}
        </MathRenderer>
      );
      
      inlineLastIndex = match.index! + match[0].length;
    });
    
    // Agregar el texto restante
    const remaining = remainingText.slice(inlineLastIndex);
    if (remaining) {
      parts.push(remaining);
    }
    
    return parts.length > 0 ? parts : [text];
  };
  
  return { processText };
};

export default MathRenderer;
