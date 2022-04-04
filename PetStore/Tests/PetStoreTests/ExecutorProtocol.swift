//
//  ExecutorProtocol.swift
//  
//
//  Created by John Scott on 05/04/2022.
//

import Foundation
@testable import PetStore

protocol ExecutorProtocol {
    func execute<T>(endpoint: PetStore.Endpoint<T>) async throws -> T
}
