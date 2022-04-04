enum PetStore {
    enum Operation {
        case listPets(limit: Int32)
        case createPets
        case showPetById(petId: PetId)

        func path(description: (Any) -> String) -> String {
            switch self {
            case .listPets(let limit):
                return "/pets"
            case .createPets:
                return "/pets"
            case .showPetById(let petId):
                return "/pets/\(description(petId))"
            }
        }
    }

    struct Endpoint<Response> { 
        let operation: Operation
        let method: String
        let body: Any?

        static func listPets(limit: Int32) -> Endpoint<Pets> { 
            .init(operation: .listPets(limit: limit),
                     method: "GET",
                       body: nil)
        }

        static func createPets(_ body: Pet) -> Endpoint<PetId> { 
            .init(operation: .createPets,
                     method: "POST",
                       body: body)
        }

        static func showPetById(petId: PetId) -> Endpoint<Pets> { 
            .init(operation: .showPetById(petId: petId),
                     method: "GET",
                       body: nil)
        }
    }

    struct Pet: Codable {
        let id: PetId
        let name: String
        let tag: String?

        enum CodingKeys: String, CodingKey {
            case id = "id"
            case name = "name"
            case tag = "tag"
        }
    }

    typealias Pets = [Pet]

    typealias PetId = String

    struct Error: Codable {
        let code: Int32
        let message: String

        enum CodingKeys: String, CodingKey {
            case code = "code"
            case message = "message"
        }
    }
}
