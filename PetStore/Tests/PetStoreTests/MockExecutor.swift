//
//  MockExecutor.swift
//  
//
//  Created by John Scott on 05/04/2022.
//

import Foundation
@testable import PetStore

enum PetError: Error {
    case petNotFound
    case typeMismatch
}

class MockExecutor: ExecutorProtocol {

    var pets: [PetStore.PetId:PetStore.Pet] = [:]
    
    func execute<T>(endpoint: PetStore.Endpoint<T>) async throws -> T {
        switch endpoint.operation {
        case .listPets(_):
            return pets.values as! T
        case .createPets:
            guard let pet = endpoint.body as? PetStore.Pet else { throw PetError.typeMismatch }
            pets[pet.id] = pet
            return () as! T
        case .showPetById(petId: let petId):
            guard let pet = pets[petId] else { throw PetError.petNotFound }
            return pet as! T
        }
    }
}

