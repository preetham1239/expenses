import React, { useState } from "react";
import axios from "axios";

const FileUpload = ({ onUploadSuccess }) => {
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState(null);
    const [uploadResult, setUploadResult] = useState(null);

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        setFile(selectedFile);
        setError(null);
        setUploadResult(null);
    };

    const handleUpload = async (e) => {
        e.preventDefault();

        if (!file) {
            setError("Please select a file first.");
            return;
        }

        // Check file type
        const allowedTypes = [
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv'
        ];

        if (!allowedTypes.includes(file.type)) {
            setError("Please upload an Excel or CSV file.");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        setUploading(true);
        setError(null);

        try {
            const response = await axios.post("https://localhost:8000/upload", formData, {
                headers: {
                    "Content-Type": "multipart/form-data"
                },
                withCredentials: true
            });

            setUploadResult(response.data);
            setFile(null);

            // Reset file input
            document.getElementById("file-upload").value = "";

            // Call the success callback if provided
            if (onUploadSuccess && typeof onUploadSuccess === 'function') {
                onUploadSuccess(response.data);
            }

        } catch (err) {
            console.error("Error uploading file:", err);

            let errorMessage = "Failed to upload file.";
            if (err.response && err.response.data && err.response.data.error) {
                errorMessage = err.response.data.error;
            } else if (err.message) {
                errorMessage = err.message;
            }

            setError(errorMessage);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="file-upload-container" style={{ margin: "20px", padding: "20px", border: "1px solid #eaeaea", borderRadius: "8px" }}>
            <h2>Upload Transaction Data</h2>
            <p>Upload your transaction data in Excel (.xlsx, .xls) or CSV format.</p>

            {error && (
                <div style={{
                    backgroundColor: "#ffebee",
                    color: "#c62828",
                    padding: "10px",
                    borderRadius: "4px",
                    marginBottom: "15px"
                }}>
                    <p style={{ margin: 0 }}><strong>Error:</strong> {error}</p>
                </div>
            )}

            {uploadResult && uploadResult.success && (
                <div style={{
                    backgroundColor: "#e8f5e9",
                    color: "#2e7d32",
                    padding: "10px",
                    borderRadius: "4px",
                    marginBottom: "15px"
                }}>
                    <p style={{ margin: 0 }}><strong>Success!</strong> {uploadResult.message}</p>
                    {uploadResult.count && (
                        <p style={{ margin: "5px 0 0 0" }}>Imported {uploadResult.count} transactions.</p>
                    )}
                </div>
            )}

            <form onSubmit={handleUpload}>
                <div style={{ marginBottom: "15px" }}>
                    <input
                        type="file"
                        id="file-upload"
                        accept=".xlsx,.xls,.csv"
                        onChange={handleFileChange}
                        style={{
                            display: "block",
                            margin: "10px 0"
                        }}
                    />
                    <small style={{ color: "#757575" }}>
                        Accepted formats: .xlsx, .xls, .csv
                    </small>
                </div>

                <button
                    type="submit"
                    disabled={!file || uploading}
                    style={{
                        padding: "10px 15px",
                        backgroundColor: (!file || uploading) ? "#cccccc" : "#4CAF50",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: (!file || uploading) ? "not-allowed" : "pointer",
                        display: "inline-flex",
                        alignItems: "center"
                    }}
                >
                    {uploading ? "Uploading..." : "Upload File"}
                </button>
            </form>

            {uploadResult && uploadResult.preview && (
                <div style={{ marginTop: "20px" }}>
                    <h3>Preview of Imported Data:</h3>
                    <div style={{ overflowX: "auto" }}>
                        <table style={{
                            width: "100%",
                            borderCollapse: "collapse",
                            fontSize: "14px"
                        }}>
                            <thead>
                            <tr>
                                <th style={{
                                    border: "1px solid #ddd",
                                    padding: "8px",
                                    backgroundColor: "#f2f2f2",
                                    textAlign: "left"
                                }}>Date</th>
                                <th style={{
                                    border: "1px solid #ddd",
                                    padding: "8px",
                                    backgroundColor: "#f2f2f2",
                                    textAlign: "left"
                                }}>Name</th>
                                <th style={{
                                    border: "1px solid #ddd",
                                    padding: "8px",
                                    backgroundColor: "#f2f2f2",
                                    textAlign: "left"
                                }}>Amount</th>
                                <th style={{
                                    border: "1px solid #ddd",
                                    padding: "8px",
                                    backgroundColor: "#f2f2f2",
                                    textAlign: "left"
                                }}>Category</th>
                            </tr>
                            </thead>
                            <tbody>
                            {uploadResult.preview.map((row, index) => (
                                <tr key={index}>
                                    <td style={{
                                        border: "1px solid #ddd",
                                        padding: "8px"
                                    }}>{new Date(row.date).toLocaleDateString()}</td>
                                    <td style={{
                                        border: "1px solid #ddd",
                                        padding: "8px"
                                    }}>{row.name}</td>
                                    <td style={{
                                        border: "1px solid #ddd",
                                        padding: "8px"
                                    }}>${parseFloat(row.amount).toFixed(2)}</td>
                                    <td style={{
                                        border: "1px solid #ddd",
                                        padding: "8px"
                                    }}>{row.category}</td>
                                </tr>
                            ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            <div style={{
                marginTop: "20px",
                backgroundColor: "#f5f5f5",
                padding: "15px",
                borderRadius: "4px",
                fontSize: "14px"
            }}>
                <h3 style={{ margin: "0 0 10px 0" }}>File Format Guidelines:</h3>
                <ul style={{ margin: 0, paddingLeft: "20px" }}>
                    <li>Your file should include columns for transaction details</li>
                    <li>Required columns: transaction ID, name/description, amount, and date</li>
                    <li>Optional columns: category, account ID</li>
                    <li>The system will try to map common column names automatically</li>
                    <li>Dates should be in a standard format (YYYY-MM-DD preferred)</li>
                </ul>
            </div>
        </div>
    );
};

export default FileUpload;
