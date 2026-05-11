import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

export function getApiErrorMessage(
  error
) {
  const detail =
    error?.response?.data
      ?.detail;

  if (
    typeof detail ===
    "string"
  ) {
    return detail;
  }

  if (
    Array.isArray(
      detail
    )
  ) {
    return detail
      .map(
        (item) =>
          item?.msg ||
          JSON.stringify(
            item
          )
      )
      .join(
        "; "
      );
  }

  if (
    detail &&
    typeof detail ===
      "object"
  ) {
    return (
      detail.message ||
      JSON.stringify(
        detail
      )
    );
  }

  return (
    error?.message ||
    "Request failed"
  );
}

export const getHealth =
  async () => {
    const response =
      await api.get(
        "/chats"
      );

    return response.data;
  };

export const createChat = async () => {
  const response = await api.post("/chats");
  return response.data;
};

export const listChats = async () => {
  const response = await api.get("/chats");
  return response.data;
};

export const getChat = async (chatId) => {
  const response = await api.get(`/chats/${chatId}`);
  return response.data;
};

export const deleteChat = async (chatId) => {
  const response = await api.delete(`/chats/${chatId}`);
  return response.data;
};

export const resetChat = async (chatId) => {
  const response = await api.post(`/chats/${chatId}/reset`);
  return response.data;
};

export const getRepositoryState = async (chatId) => {
  const response = await api.get(`/chats/${chatId}/repository-state`);
  return response.data;
};

export const getDependencyGraph = async (chatId) => {
  const response = await api.get(`/chats/${chatId}/dependency-graph`);
  return response.data;
};

export const getAnalytics = async (chatId) => {
  const response = await api.get(`/chats/${chatId}/analytics`);
  return response.data;
};

export const ingestRepository = async (chatId, repoUrl) => {
  const response = await api.post(`/chats/${chatId}/ingest`, { repo_url: repoUrl });
  return response.data;
};

export const cancelIngestion = async (chatId) => {
  const response = await api.post(`/chats/${chatId}/ingest/cancel`);
  return response.data;
};

export const getIngestionStatus = async (chatId) => {
  const response = await api.get(`/chats/${chatId}/ingest/status`);
  return response.data;
};

export const askQuestion = async (chatId, query, topK = 2) => {
  const response = await api.post(`/chats/${chatId}/ask`, { query, top_k: topK });
  return response.data;
};

export const searchRepository = async (chatId, query, topK = 2) => {
  const response = await api.post(`/chats/${chatId}/search`, { query, top_k: topK });
  return response.data;
};

export const getExplorationData = async (chatId) => {
  const response = await api.get(`/chats/${chatId}/explore`);
  return response.data;
};

export const getFileInspect = async (chatId, filePath) => {
  const response = await api.get(`/chats/${chatId}/file-inspect`, { params: { file_path: filePath } });
  return response.data;
};

export default api;
