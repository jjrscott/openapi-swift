//
//  Executor.swift
//
//  Created by John Scott on 03/04/2022.
//

import Foundation
@testable import PetStore

struct Executor: ExecutorProtocol {
    let baseUrl: URL
    let encoder: JSONEncoder
    let decoder: JSONDecoder
    let session: URLSession

    func execute<T>(endpoint: PetStore.Endpoint<T>) async throws -> T {
        let path = endpoint.operation.path { value in
            let value = String(describing: value)
            return value.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? value
        }
        
        var request = URLRequest(url: baseUrl.appendingPathComponent(path))
        request.httpMethod = endpoint.method
        if let body = endpoint.body as? Encodable {
            let encoder = JSONEncoder()
            request.httpBody = try body.encode(to: encoder)
        }
        let (data, _) = try await session.data(for: request, delegate: nil)
        return try decoder.decode(T.self, from: data) { _ in
            guard T.self is Void.Type else { fatalError() }
            return () as! T
        }
    }
}
