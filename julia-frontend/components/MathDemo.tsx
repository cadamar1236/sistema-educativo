import React, { useState } from 'react';
import { MathRenderer } from '@/components/ui/MathRenderer';
import { useMathProcessor } from '@/hooks/useMathProcessor';
import { Button, Card, CardBody, Input, Textarea } from '@nextui-org/react';

/**
 * Componente de demostración para probar el rendering matemático
 */
export default function MathDemo() {
  const { processMessage } = useMathProcessor();
  const [testText, setTestText] = useState('');
  const [processedText, setProcessedText] = useState('');

  // Ejemplos de texto con problemas de Unicode
  const examples = [
    {
      title: "Fórmula cuadrática con Unicode",
      text: "La fórmula cuadrática es: x\u202f=\u202f\u2212b\u202f±\u202f√(b²\u2212\u20624ac)\u20622a"
    },
    {
      title: "Integral definida",
      text: "∫₀¹\u202fx²\u202fdx\u202f=\u202f1/3"
    },
    {
      title: "Límite matemático",
      text: "lim\u202fx→∞\u202f(1\u202f+\u202f1/x)ˣ\u202f=\u202fe"
    },
    {
      title: "Derivada con Unicode",
      text: "Si f(x)\u202f=\u202fx³\u202f+\u202f2x²\u202f−\u202f5x\u202f+\u202f1, entonces f'(x)\u202f=\u202f3x²\u202f+\u202f4x\u202f−\u202f5"
    },
    {
      title: "Sistema de ecuaciones",
      text: "Sistema:\u202f2x\u202f+\u202f3y\u202f=\u202f7\u202f\u202f\u202fx\u202f−\u202fy\u202f=\u202f1"
    }
  ];

  const processText = () => {
    const message = { 
      id: '1', 
      content: testText, 
      type: 'agent' as const, 
      timestamp: new Date() 
    };
    const processed = processMessage(message);
    setProcessedText(processed.content);
  };

  const loadExample = (example: typeof examples[0]) => {
    setTestText(example.text);
    const message = { 
      id: '1', 
      content: example.text, 
      type: 'agent' as const, 
      timestamp: new Date() 
    };
    const processed = processMessage(message);
    setProcessedText(processed.content);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold mb-6">🧮 Demo de Rendering Matemático</h1>
      
      {/* Ejemplos predefinidos */}
      <Card>
        <CardBody>
          <h2 className="text-lg font-semibold mb-4">📝 Ejemplos con problemas de Unicode</h2>
          <div className="grid gap-3">
            {examples.map((example, index) => (
              <div key={index} className="flex gap-2 items-center">
                <Button
                  size="sm"
                  color="primary"
                  variant="flat"
                  onPress={() => loadExample(example)}
                  className="min-w-40"
                >
                  {example.title}
                </Button>
                <code className="text-xs bg-gray-100 p-1 rounded flex-1 truncate">
                  {example.text}
                </code>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>

      {/* Input de prueba */}
      <Card>
        <CardBody>
          <h2 className="text-lg font-semibold mb-4">🔧 Probar texto personalizado</h2>
          <div className="space-y-3">
            <Textarea
              label="Texto con matemáticas (puede contener Unicode problemático)"
              placeholder="Ingresa texto con fórmulas matemáticas..."
              value={testText}
              onChange={(e) => setTestText(e.target.value)}
              rows={3}
            />
            <Button color="primary" onPress={processText} disabled={!testText.trim()}>
              🔄 Procesar Texto
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* Comparación antes/después */}
      {processedText && (
        <div className="grid md:grid-cols-2 gap-4">
          <Card>
            <CardBody>
              <h3 className="font-semibold mb-2 text-red-600">❌ Texto Original (con problemas)</h3>
              <div className="bg-red-50 p-3 rounded border text-sm font-mono">
                {testText}
              </div>
            </CardBody>
          </Card>
          
          <Card>
            <CardBody>
              <h3 className="font-semibold mb-2 text-green-600">✅ Texto Procesado (limpio)</h3>
              <div className="bg-green-50 p-3 rounded border">
                <MathRenderer content={processedText} />
              </div>
            </CardBody>
          </Card>
        </div>
      )}

      {/* Información técnica */}
      <Card>
        <CardBody>
          <h2 className="text-lg font-semibold mb-4">ℹ️ Información Técnica</h2>
          <div className="text-sm space-y-2">
            <p><strong>Caracteres Unicode problemáticos detectados:</strong></p>
            <ul className="list-disc list-inside space-y-1 text-gray-600">
              <li><code>\u202f</code> - Narrow No-Break Space (espacio estrecho sin salto)</li>
              <li><code>\u2062</code> - Invisible Times (multiplicación invisible)</li>
              <li><code>\u2063</code> - Invisible Separator (separador invisible)</li>
              <li><code>\u2061</code> - Function Application (aplicación de función)</li>
            </ul>
            <p className="mt-3">
              <strong>Solución:</strong> El componente <code>useMathProcessor</code> limpia automáticamente estos caracteres 
              y mejora el formato para su renderizado con KaTeX.
            </p>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
