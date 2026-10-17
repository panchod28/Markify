// Prepara el Markdown para la vista previa renderizada. El Markdown crudo (y el .md que se guarda) no se toca.
//
// markitdown y el sidecar insertan comentarios HTML (`<!-- Slide number: N -->`, `<!-- Markify: página N … -->`) que
// react-markdown muestra como texto. En la vista renderizada los marcadores de diapositiva pasan a ser una línea
// horizontal (separa las diapositivas) y el resto de comentarios se oculta; el aviso de página fallida sigue
// disponible en el icono de avisos y en la vista de Markdown crudo.
export function toRenderedMarkdown(markdown: string): string {
  return markdown
    .replace(/<!--\s*Slide number:\s*\d+\s*-->/g, '\n\n---\n\n')
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/<!--[\s\S]*$/, '') // comentario cortado por el límite de la vista previa
    .replace(/^\s*(---\s*)+/, ''); // sin línea al principio del documento
}
