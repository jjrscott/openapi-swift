//
//  File.swift
//  
//
//  Created by Filip Sakel on 27/03/2022.
//  https://forums.swift.org/t/anycodable-efficacy/49055/7
//

import Foundation

// The existential box is opened on `Encodable` methods,
// so we can get access to `Self: Encodable` instead of `Encodable`.
extension Encodable {
    func encode(to jsonEncoder: JSONEncoder) throws -> Data {
        try jsonEncoder.encode(self)
    }
}

extension JSONEncoder {
    func encode<T>(_ value: T, fallback: (Any) throws -> Data) throws -> Data {
        guard let value = value as? Encodable else {
            return try fallback(value)
        }
        
        // Just relay to our existential-opening proxy method.
        return try value.encode(to: self)
    }
}

extension Decodable {
    // The same as for `Encodable`.
    static func decode(to jsonDecoder: JSONDecoder, data: Data) throws -> Self {
        try jsonDecoder.decode(self, from: data)
    }
}

extension JSONDecoder {
    func decode<T>(_ type: T.Type, from data: Data, fallback: (Data) throws -> T) throws -> T {
        guard let decodableType = type as? Decodable.Type else {
            return try fallback(data)
        }
        
        // Unfortunately, we do have to do an unsafe cast, but it's
        // all in one place. We do the cast, get a `Decodable` box,
        // operate on it and then cast in *one* function.
        return try decodableType.decode(to: self, data: data) as! T
    }
}
