/**
 * Google Apps Script for Competition Hub (SGA Cakrawala University)
 *
 * Menu interaktif untuk tim penelaah Subdivisi Lomba di Google Sheets.
 * Memungkinkan pemindahan lomba berstatus approved ke Master Data dalam 1-klik.
 */

const AUDIT_SHEET_NAME = "Tab Audit";
const MASTER_SHEET_NAME = "Master Data Lomba";
const ARCHIVE_SHEET_NAME = "Arsip Reject";

/**
 * Otomatis menambahkan custom menu saat spreadsheet dibuka.
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu("🏆 Competition Hub")
    .addItem("✅ Approve Baris Terpilih", "approveSelectedRows")
    .addItem("⚡ Batch Approve Semua Hijau (AUTO_APPROVE)", "batchApproveGreenRows")
    .addSeparator()
    .addItem("❌ Reject Baris Terpilih", "rejectSelectedRows")
    .addToUi();
}

/**
 * Mengambil atau membuat sheet target jika belum ada.
 */
function getOrCreateSheet(ss, name, headers) {
  let sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    if (headers && headers.length > 0) {
      sheet.appendRow(headers);
      sheet.getRange(1, 1, 1, headers.length).setFontWeight("bold");
    }
  }
  return sheet;
}

/**
 * Memindahkan baris yang dipilih pengguna dari Tab Audit ke Master Data Lomba.
 */
function approveSelectedRows() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const auditSheet = ss.getSheetByName(AUDIT_SHEET_NAME);
  const ui = SpreadsheetApp.getUi();

  if (!auditSheet || ss.getActiveSheet().getName() !== AUDIT_SHEET_NAME) {
    ui.alert("Peringatan", "Aksi ini hanya dapat dijalankan di lembar kerja '" + AUDIT_SHEET_NAME + "'.", ui.ButtonSet.OK);
    return;
  }

  const selection = auditSheet.getActiveRange();
  const startRow = selection.getRow();
  const numRows = selection.getNumRows();

  if (startRow === 1) {
    ui.alert("Peringatan", "Baris header tidak dapat di-approve.", ui.ButtonSet.OK);
    return;
  }

  const auditHeaders = auditSheet.getRange(1, 1, 1, auditSheet.getLastColumn()).getValues()[0];
  const masterSheet = getOrCreateSheet(ss, MASTER_SHEET_NAME, auditHeaders);

  const rowsToMove = auditSheet.getRange(startRow, 1, numRows, auditSheet.getLastColumn()).getValues();

  // Tambahkan ke Master Data
  for (let i = 0; i < rowsToMove.length; i++) {
    masterSheet.appendRow(rowsToMove[i]);
  }

  // Hapus dari Tab Audit dari baris terbawah ke teratas
  auditSheet.deleteRows(startRow, numRows);

  ui.alert("Berhasil", numRows + " lomba berhasil di-approve dan dipindahkan ke '" + MASTER_SHEET_NAME + "'.", ui.ButtonSet.OK);
}

/**
 * Memindahkan semua lomba berstatus AUTO_APPROVE (hijau) sekaligus ke Master Data.
 */
function batchApproveGreenRows() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const auditSheet = ss.getSheetByName(AUDIT_SHEET_NAME);
  const ui = SpreadsheetApp.getUi();

  if (!auditSheet) {
    ui.alert("Eror", "Lembar '" + AUDIT_SHEET_NAME + "' tidak ditemukan.", ui.ButtonSet.OK);
    return;
  }

  const data = auditSheet.getDataRange().getValues();
  if (data.length <= 1) {
    ui.alert("Info", "Tidak ada data lomba pada Tab Audit.", ui.ButtonSet.OK);
    return;
  }

  const headers = data[0];
  const statusColIndex = headers.indexOf("Status Review");

  if (statusColIndex === -1) {
    ui.alert("Eror", "Kolom 'Status Review' tidak ditemukan.", ui.ButtonSet.OK);
    return;
  }

  const masterSheet = getOrCreateSheet(ss, MASTER_SHEET_NAME, headers);

  let approvedCount = 0;
  // Loop dari baris paling bawah ke atas agar penghapusan baris tidak merusak indeks
  for (let r = data.length - 1; r >= 1; r--) {
    const rowStatus = String(data[r][statusColIndex]).trim().toUpperCase();
    if (rowStatus === "AUTO_APPROVE") {
      masterSheet.appendRow(data[r]);
      auditSheet.deleteRow(r + 1);
      approvedCount++;
    }
  }

  if (approvedCount > 0) {
    ui.alert("Sukses", approvedCount + " lomba AUTO_APPROVE berhasil dipindahkan ke Master Data Lomba!", ui.ButtonSet.OK);
  } else {
    ui.alert("Info", "Tidak ditemukan baris dengan status AUTO_APPROVE.", ui.ButtonSet.OK);
  }
}

/**
 * Menandai dan mengarsipkan baris yang di-reject ke sheet Arsip Reject.
 */
function rejectSelectedRows() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const auditSheet = ss.getSheetByName(AUDIT_SHEET_NAME);
  const ui = SpreadsheetApp.getUi();

  if (!auditSheet || ss.getActiveSheet().getName() !== AUDIT_SHEET_NAME) {
    ui.alert("Peringatan", "Aksi ini hanya dapat dijalankan di lembar kerja '" + AUDIT_SHEET_NAME + "'.", ui.ButtonSet.OK);
    return;
  }

  const selection = auditSheet.getActiveRange();
  const startRow = selection.getRow();
  const numRows = selection.getNumRows();

  if (startRow === 1) return;

  const headers = auditSheet.getRange(1, 1, 1, auditSheet.getLastColumn()).getValues()[0];
  const archiveSheet = getOrCreateSheet(ss, ARCHIVE_SHEET_NAME, headers);

  const rowsToMove = auditSheet.getRange(startRow, 1, numRows, auditSheet.getLastColumn()).getValues();

  for (let i = 0; i < rowsToMove.length; i++) {
    archiveSheet.appendRow(rowsToMove[i]);
  }

  auditSheet.deleteRows(startRow, numRows);

  ui.alert("Selesai", numRows + " lomba telah dipindahkan ke '" + ARCHIVE_SHEET_NAME + "'.", ui.ButtonSet.OK);
}
