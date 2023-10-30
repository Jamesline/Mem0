import hashlib
import pytest
from llama_index.readers.schema.base import Document

from embedchain.loaders.json import JSONLoader


def test_load_data(mocker):
    content = "temp.json"

    mock_document = {
        "doc_id": hashlib.sha256((content + ", ".join(["content1", "content2"])).encode()).hexdigest(),
        "data": [
            {"content": "content1", "meta_data": {"url": content}},
            {"content": "content2", "meta_data": {"url": content}},
        ],
    }
    
    mocker.patch("embedchain.loaders.json.JSONLoader.load_data", return_value=mock_document)

    json_loader = JSONLoader()

    result = json_loader.load_data(content)

    assert "doc_id" in result
    assert "data" in result

    expected_data = [
        {"content": "content1", "meta_data": {"url": content}},
        {"content": "content2", "meta_data": {"url": content}},
    ]

    assert result["data"] == expected_data

    expected_doc_id = hashlib.sha256((content + ", ".join(["content1", "content2"])).encode()).hexdigest()
    assert result["doc_id"] == expected_doc_id


def test_load_data_url(mocker):
    content = "https://example.com/posts.json"

    mocker.patch("os.path.isfile", return_value=False)  # Mocking os.path.isfile to simulate a URL case
    mocker.patch(
        "llama_hub.jsondata.base.JSONDataReader.load_data",
        return_value=[Document(text="content1"), Document(text="content2")],
    )

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"document1": "content1", "document2": "content2"}

    mocker.patch("requests.get", return_value=mock_response)

    result = JSONLoader.load_data(content)

    assert "doc_id" in result
    assert "data" in result

    expected_data = [
        {"content": "content1", "meta_data": {"url": content}},
        {"content": "content2", "meta_data": {"url": content}},
    ]

    assert result["data"] == expected_data

    expected_doc_id = hashlib.sha256((content + ", ".join(["content1", "content2"])).encode()).hexdigest()
    assert result["doc_id"] == expected_doc_id


def test_load_data_invalid_content(mocker):
    mocker.patch("os.path.isfile", return_value=False)
    mocker.patch("requests.get")

    content = "123"

    with pytest.raises(ValueError, match="Invalid content to load json data from"):
        JSONLoader.load_data(content)


def test_load_data_invalid_url(mocker):
    mocker.patch("os.path.isfile", return_value=False)

    mock_response = mocker.Mock()
    mock_response.status_code = 404
    mocker.patch("requests.get", return_value=mock_response)

    content = "http://invalid-url.com/"

    with pytest.raises(ValueError, match=f"Invalid content to load json data from: {content}"):
        JSONLoader.load_data(content)
