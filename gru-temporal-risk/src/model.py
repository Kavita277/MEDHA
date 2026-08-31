import torch
import torch.nn as nn


class GRUModel(nn.Module):

    def __init__(self, input_size, hidden_size=64, num_layers=1, dropout=0.3):
        super().__init__()

        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        _, hidden_state = self.gru(x)
        last_hidden_state = hidden_state[-1]
        return self.fc(self.dropout(last_hidden_state)).squeeze(-1)

    def predict_proba(self, x):
        return torch.sigmoid(self(x))
