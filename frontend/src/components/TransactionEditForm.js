import React, { useState, useEffect } from 'react';

const TransactionEditForm = ({ transaction, onClose, onSave }) => {
    const [formData, setFormData] = useState({
        name: '',
        amount: '',
        date: '',
        category: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Initialize form data when transaction changes
    useEffect(() => {
        if (transaction) {
            setFormData({
                name: transaction.name || '',
                amount: transaction.amount ? Math.abs(parseFloat(transaction.amount)).toString() : '',
                date: transaction.date ? transaction.date.split('T')[0] : '',
                category: Array.isArray(transaction.category) ? transaction.category[0] : transaction.category || 'Uncategorized'
            });
        }
    }, [transaction]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            // Validate form
            if (!formData.name || !formData.amount || !formData.date) {
                throw new Error('Please fill out all required fields');
            }

            // Create updated transaction object
            const updatedTransaction = {
                ...transaction,
                name: formData.name,
                amount: parseFloat(formData.amount), // Keep amount positive for now
                date: formData.date,
                category: formData.category
            };

            // Call the save function provided by parent
            await onSave(updatedTransaction);
            onClose();
        } catch (err) {
            setError(err.message || 'Failed to save transaction');
        } finally {
            setLoading(false);
        }
    };

    // Common style for inputs
    const inputStyle = {
        width: '100%',
        padding: '10px',
        border: '1px solid #ddd',
        borderRadius: '4px',
        fontSize: '16px',
        marginBottom: '10px'
    };

    // Common style for labels
    const labelStyle = {
        display: 'block',
        marginBottom: '5px',
        fontWeight: 'bold'
    };

    return (
        <div className="popup-overlay" style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000
        }}>
            <div className="popup-content" style={{
                backgroundColor: 'white',
                borderRadius: '8px',
                padding: '20px',
                width: '90%',
                maxWidth: '500px',
                maxHeight: '80vh',
                overflowY: 'auto',
                boxShadow: '0 2px 10px rgba(0, 0, 0, 0.2)'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                    <h2 style={{ margin: 0 }}>Edit Transaction</h2>
                    <button
                        onClick={onClose}
                        style={{
                            background: 'none',
                            border: 'none',
                            fontSize: '24px',
                            cursor: 'pointer'
                        }}
                    >
                        ×
                    </button>
                </div>

                {error && (
                    <div style={{
                        padding: '10px',
                        backgroundColor: '#ffebee',
                        color: '#c62828',
                        borderRadius: '4px',
                        marginBottom: '15px'
                    }}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div style={{ marginBottom: '15px' }}>
                        <label style={labelStyle} htmlFor="name">
                            Description *
                        </label>
                        <input
                            id="name"
                            name="name"
                            type="text"
                            value={formData.name}
                            onChange={handleChange}
                            style={inputStyle}
                            required
                        />
                    </div>

                    <div style={{ marginBottom: '15px' }}>
                        <label style={labelStyle} htmlFor="amount">
                            Amount *
                        </label>
                        <input
                            id="amount"
                            name="amount"
                            type="number"
                            step="0.01"
                            value={formData.amount}
                            onChange={handleChange}
                            style={inputStyle}
                            required
                        />
                    </div>

                    <div style={{ marginBottom: '15px' }}>
                        <label style={labelStyle} htmlFor="date">
                            Date *
                        </label>
                        <input
                            id="date"
                            name="date"
                            type="date"
                            value={formData.date}
                            onChange={handleChange}
                            style={inputStyle}
                            required
                        />
                    </div>

                    <div style={{ marginBottom: '20px' }}>
                        <label style={labelStyle} htmlFor="category">
                            Category
                        </label>
                        <select
                            id="category"
                            name="category"
                            value={formData.category}
                            onChange={handleChange}
                            style={inputStyle}
                        >
                            <option value="Uncategorized">Uncategorized</option>
                            <option value="Food and Drink">Food and Drink</option>
                            <option value="Transportation">Transportation</option>
                            <option value="Shopping">Shopping</option>
                            <option value="Entertainment">Entertainment</option>
                            <option value="Travel">Travel</option>
                            <option value="Groceries">Groceries</option>
                            <option value="Bills and Utilities">Bills and Utilities</option>
                            <option value="Health and Medical">Health and Medical</option>
                            <option value="Personal Care">Personal Care</option>
                            <option value="Education">Education</option>
                            <option value="Home">Home</option>
                            <option value="Gifts and Donations">Gifts and Donations</option>
                            <option value="Business">Business</option>
                            <option value="Income">Income</option>
                        </select>
                    </div>

                    <div style={{ textAlign: 'right' }}>
                        <button
                            type="button"
                            onClick={onClose}
                            style={{
                                padding: '10px 15px',
                                backgroundColor: '#f5f5f5',
                                color: 'black',
                                border: '1px solid #ddd',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                marginRight: '10px'
                            }}
                            disabled={loading}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            style={{
                                padding: '10px 15px',
                                backgroundColor: '#4CAF50',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: loading ? 'not-allowed' : 'pointer',
                                opacity: loading ? 0.7 : 1
                            }}
                            disabled={loading}
                        >
                            {loading ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default TransactionEditForm;
