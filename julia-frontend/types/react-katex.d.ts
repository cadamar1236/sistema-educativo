declare module 'react-katex' {
  import { ComponentType } from 'react';

  export interface KaTeXProps {
    children?: string;
    math?: string;
    settings?: any;
    renderError?: (error: Error) => string | React.ReactElement;
    as?: string;
  }

  export const InlineMath: ComponentType<KaTeXProps>;
  export const BlockMath: ComponentType<KaTeXProps>;
}
