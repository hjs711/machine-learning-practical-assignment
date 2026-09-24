const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
        AlignmentType, BorderStyle, WidthType, ShadingType, HeadingLevel, PageBreak } = require('docx');
const fs = require('fs');

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: "1F4E78" },
        paragraph: { spacing: { before: 360, after: 240 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: "2E75B6" },
        paragraph: { spacing: { before: 280, after: 180 }, outlineLevel: 1 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 2880, after: 720 },
        children: [new TextRun({ text: "Machine Learning Course Practice", size: 48, bold: true })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 240 },
        children: [new TextRun({ text: "First Stage Inspection", size: 36, bold: true, color: "2E75B6" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 1440 },
        children: [new TextRun({ text: "Data Analysis + Feature Engineering", size: 28, color: "5B9BD5" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 1440, after: 240 },
        children: [new TextRun({ text: "Dataset: USGS 01047000 Streamflow Prediction", size: 24 })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 2880 },
        children: [new TextRun({ text: "Date: October 8, 2024", size: 22 })]
      }),
      
      new Paragraph({ children: [new PageBreak()] }),
      
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Completion Status Overview")] }),
      
      new Paragraph({
        spacing: { before: 240, after: 240 },
        children: [new TextRun({ text: "All 8 subtasks completed successfully (100% completion rate)", bold: true, size: 26, color: "00B050" })]
      }),
      
      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [1200, 5826, 1200, 800],
        rows: [
          new TableRow({
            children: [
              new TableCell({
                borders, width: { size: 1200, type: WidthType.DXA },
                shading: { fill: "4472C4", type: ShadingType.CLEAR },
                margins: { top: 120, bottom: 120, left: 120, right: 120 },
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Task ID", bold: true, color: "FFFFFF" })] })]
              }),
              new TableCell({
                borders, width: { size: 5826, type: WidthType.DXA },
                shading: { fill: "4472C4", type: ShadingType.CLEAR },
                margins: { top: 120, bottom: 120, left: 120, right: 120 },
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Subtask", bold: true, color: "FFFFFF" })] })]
              }),
              new TableCell({
                borders, width: { size: 1200, type: WidthType.DXA },
                shading: { fill: "4472C4", type: ShadingType.CLEAR },
                margins: { top: 120, bottom: 120, left: 120, right: 120 },
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Status", bold: true, color: "FFFFFF" })] })]
              }),
              new TableCell({
                borders, width: { size: 800, type: WidthType.DXA },
                shading: { fill: "4472C4", type: ShadingType.CLEAR },
                margins: { top: 120, bottom: 120, left: 120, right: 120 },
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Score", bold: true, color: "FFFFFF" })] })]
              })
            ]
          }),
          ...generateTaskRows()
        ]
      }),
      
      new Paragraph({ spacing: { before: 360, after: 180 }, children: [
        new TextRun({ text: "Summary:", bold: true, size: 26 })
      ]}),
      new Paragraph({ spacing: { after: 120 }, children: [new TextRun("- Data Analysis: 5/5 subtasks completed")] }),
      new Paragraph({ spacing: { after: 120 }, children: [new TextRun("- Feature Engineering: 3/3 subtasks completed")] }),
      new Paragraph({ spacing: { after: 120 }, children: [new TextRun("- Extra: Lag correlation analysis, method comparison, full modeling")] }),
      
      new Paragraph({ children: [new PageBreak()] })
    ]
  }]
});

function generateTaskRows() {
  const tasks = [
    ["Task 1", "Understand field meanings (Chinese)", "Done", "Pass"],
    ["Task 2", "Time series visualization (all columns)", "Done", "Pass"],
    ["Task 3", "Histogram (all columns)", "Done", "Pass"],
    ["Task 4", "Boxplot (all columns)", "Done", "Pass"],
    ["Task 5", "Pearson correlation heatmap (with lags)", "Done", "Pass"],
    ["Task 6", "Season/month encoding + lag + rolling features", "Done", "Pass"],
    ["Task 7", "Feature normalization (Min-Max or Z-score)", "Done", "Pass"],
    ["Task 8", "Feature selection (Pearson or MI)", "Done", "Pass"]
  ];
  
  return tasks.map(([num, task, status, score]) => new TableRow({
    children: [
      new TableCell({
        borders, width: { size: 1200, type: WidthType.DXA },
        shading: { fill: "F2F2F2", type: ShadingType.CLEAR },
        margins: { top: 100, bottom: 100, left: 120, right: 120 },
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun(num)] })]
      }),
      new TableCell({
        borders, width: { size: 5826, type: WidthType.DXA },
        margins: { top: 100, bottom: 100, left: 120, right: 120 },
        children: [new Paragraph({ children: [new TextRun(task)] })]
      }),
      new TableCell({
        borders, width: { size: 1200, type: WidthType.DXA },
        shading: { fill: "E2F0D9", type: ShadingType.CLEAR },
        margins: { top: 100, bottom: 100, left: 120, right: 120 },
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: status, bold: true, color: "00B050" })] })]
      }),
      new TableCell({
        borders, width: { size: 800, type: WidthType.DXA },
        shading: { fill: "E2F0D9", type: ShadingType.CLEAR },
        margins: { top: 100, bottom: 100, left: 120, right: 120 },
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: score, bold: true })] })]
      })
    ]
  }));
}

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("inspection_report_part1.docx", buffer);
  console.log("Part 1 generated successfully");
});
